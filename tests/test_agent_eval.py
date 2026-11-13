"""Agent vs one-shot harness: scoring, resumable appends and the paired summary,
with a fake LLM and a fake pipeline (no network, no key, no quota)."""

import json

import pytest

from core.config import load_settings
from evaluation.agent_eval import load_rows, numbers, run_comparison, score, summarize
from evaluation.retrieval_eval import GoldItem
from schemas.common import Chunk, RetrievedChunk

DOCS = ["de/tum/dea-msc/programme", "de/munich/residence-permit-study"]


def item(qid="c12"):
    return GoldItem(qid=qid, question="TUM DEA tuition and blocked account?", relevant_doc_ids=DOCS,
                    answer_hint="6,000 euros per semester; at least 11,904 euros.", kind="multi_hop")


class FakePipeline:
    def search(self, query, mode="hybrid_rerank", top_k=None, **_):
        return [RetrievedChunk(chunk=Chunk(chunk_id=f"c{i}", doc_id=d, source=d, title=d, section_path="s",
                                           url="https://example.org", text="6,000 euros. 11.904 euros.",
                                           token_count=5), rerank_score=0.9)
                for i, d in enumerate(DOCS)]


class Quota(Exception):
    """Stands in for the SDK's RateLimitError: is_provider_error reads the module."""


Quota.__module__ = "openai._exceptions"


class ScriptedLLM:
    """One-shot calls (plain mode) get `plain`; agent calls (JSON mode) get `agent` in order.
    `fail_after` raises Quota once that many calls were made, like a used-up daily quota;
    `switch_after` moves to a fallback model after that many calls, like a 429 in LLMClient."""

    available = True

    def __init__(self, plain, agent, fail_after=None, switch_after=None):
        self.plain, self.agent, self.fail_after, self.calls = plain, list(agent), fail_after, 0
        self.switch_after, self.model = switch_after, "fake-model"

    def complete(self, messages, json_mode=False):
        if self.fail_after is not None and self.calls >= self.fail_after:
            raise Quota("quota")
        if self.switch_after is not None and self.calls >= self.switch_after:
            self.model = "fallback-model"
        self.calls += 1
        return json.dumps(self.agent.pop(0)) if json_mode else self.plain


def agent_script():
    return [{"tool": "search_sources", "args": {"query": "tuition"}},
            {"answer": "Tuition is 6,000 euros [1]; the blocked account needs 11,904 euros [2]."}]


@pytest.fixture
def settings():
    return load_settings()


def test_numbers_normalise_separators_and_skip_markers():
    assert numbers("11,904 and 11.904 EUR, grade 2,5 or 2.5, 1,500") == {"11904", "2.5", "1500"}
    assert numbers("361,00 EUR, 7.0 or 97.00 [1] [8]") == {"361", "7", "97"}


def test_score_counts_docs_and_hint_numbers():
    s = score(item(), "6000 euros and 992 a month", [DOCS[0], "de/other"], refused=False)
    assert s == {"doc_recall": 0.5, "fact_recall": 0.5}
    assert score(item(), "", [], refused=True) == {"doc_recall": 0.0, "fact_recall": 0.0}
    no_numbers = GoldItem(qid="x", question="q", relevant_doc_ids=DOCS, answer_hint="Apply online.")
    assert score(no_numbers, "x", DOCS, refused=False)["fact_recall"] is None
    first_march = GoldItem(qid="m", question="q", relevant_doc_ids=DOCS, answer_hint="deadline 1st March")
    assert score(first_march, "Applications close 15 January [1].", DOCS, refused=False)["fact_recall"] == 0.0


def test_uncited_oneshot_answer_scores_as_a_refusal(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    run_comparison([item()], settings, FakePipeline(), ScriptedLLM("Tuition is 6,000 euros.", agent_script()), out)
    oneshot = load_rows(out)[0]
    assert oneshot["arm"] == "oneshot" and oneshot["refused"]
    assert oneshot["scores"] == {"doc_recall": 0.0, "fact_recall": 0.0}


def test_rows_are_appended_and_a_rerun_resumes(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    items = [item("a"), item("b")]
    # quota ends inside item b's agent arm: a has 3 calls, b's one-shot 1, b's agent fails on its 1st
    llm = ScriptedLLM("Tuition 6,000 euros [1].", agent_script() * 2, fail_after=4)
    written, stopped, mixed = run_comparison(items, settings, FakePipeline(), llm, out)
    assert written == 2 and stopped == "b/agent: Quota" and mixed == 0
    rows = load_rows(out)
    assert [(r["qid"], r["arm"], r["llm_calls"]) for r in rows] == [("a", "oneshot", 1), ("a", "agent", 2)]
    assert rows[1]["cited_doc_ids"] == DOCS and rows[1]["scores"] == {"doc_recall": 1.0, "fact_recall": 1.0}
    assert rows[1]["steps"] == [{"tool": "search_sources", "args": {"query": "tuition"}, "ok": True}]
    assert {r["model"] for r in rows} == {"fake-model"}
    # next day: item b runs both arms again (its lone one-shot was never written)
    llm2 = ScriptedLLM("Tuition 6,000 euros [1].", agent_script())
    written, stopped, _ = run_comparison(items, settings, FakePipeline(), llm2, out)
    assert written == 2 and stopped is None and llm2.calls == 3
    assert [(r["qid"], r["arm"]) for r in load_rows(out)][2:] == [("b", "oneshot"), ("b", "agent")]


def test_a_model_switch_inside_a_pair_drops_the_pair(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    llm = ScriptedLLM("Tuition 6,000 euros [1].", agent_script() * 2, switch_after=1)
    written, stopped, mixed = run_comparison([item("a"), item("b")], settings, FakePipeline(), llm, out)
    assert (written, stopped, mixed) == (2, None, 1)
    assert [(r["qid"], r["model"]) for r in load_rows(out)] == [("b", "fallback-model")] * 2


def test_a_harness_bug_raises_instead_of_stopping_quietly(settings, tmp_path):
    class Broken(ScriptedLLM):
        def complete(self, messages, json_mode=False):
            raise KeyError("bug")

    with pytest.raises(KeyError):
        run_comparison([item()], settings, FakePipeline(), Broken("", []), tmp_path / "rows.jsonl")


def test_a_torn_last_line_is_skipped(tmp_path):
    out = tmp_path / "rows.jsonl"
    out.write_text(json.dumps({"qid": "a", "arm": "oneshot"}) + "\n" + '{"qid": "a", "ar')
    assert load_rows(out) == [{"qid": "a", "arm": "oneshot"}]


def test_summary_pairs_items_and_reports_the_difference(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    items = [item("a"), item("b"), item("c")]
    run_comparison(items[:2], settings, FakePipeline(), ScriptedLLM("Tuition 6,000 euros [1].",
                                                                    agent_script() * 2), out)
    s = summarize(load_rows(out), items, resamples=200)
    assert s["items_paired"] == 2 and s["items_total"] == 3
    m = s["metrics"]["doc_recall"]
    assert (m["oneshot"], m["agent"], m["diff"]) == (0.5, 1.0, 0.5) and m["diff_ci"] == (0.5, 0.5)
    assert s["agent"]["llm_calls_mean"] == 2 and s["oneshot"]["models"] == ["fake-model"]


def test_script_summary_only_needs_no_key(tmp_path, monkeypatch, capsys):
    import scripts.compare_agent as script

    settings = load_settings()
    settings.agent.comparison_out = str(tmp_path / "rows.jsonl")
    settings.agent.summary_out = str(tmp_path / "summary.json")
    monkeypatch.setattr(script, "get_settings", lambda: settings)
    assert script.main(["--summary-only"]) == 0
    assert json.loads((tmp_path / "summary.json").read_text())["items_total"] == 28
    assert script.main([]) == 1  # tests blank the key: nothing runs
    with pytest.raises(SystemExit):
        script.main(["--limit", "-1"])
