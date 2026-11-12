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


class ScriptedLLM:
    """One-shot calls (plain mode) get `plain`; agent calls (JSON mode) get `agent` in order.
    `fail_after` raises once that many calls were made, like a used-up daily quota."""

    available, model = True, "fake-model"

    def __init__(self, plain, agent, fail_after=None):
        self.plain, self.agent, self.fail_after, self.calls = plain, list(agent), fail_after, 0

    def complete(self, messages, json_mode=False):
        if self.fail_after is not None and self.calls >= self.fail_after:
            raise RuntimeError("quota")
        self.calls += 1
        return json.dumps(self.agent.pop(0)) if json_mode else self.plain


def agent_script():
    return [{"tool": "search_sources", "args": {"query": "tuition"}},
            {"answer": "Tuition is 6,000 euros [1]; the blocked account needs 11,904 euros [2]."}]


@pytest.fixture
def settings():
    return load_settings()


def test_numbers_normalise_separators():
    assert numbers("11,904 and 11.904 EUR, grade 2,5 or 2.5, 1,500") == {"11904", "2.5", "1500"}


def test_score_counts_docs_and_hint_numbers():
    s = score(item(), "6000 euros and 992 a month", [DOCS[0], "de/other"], refused=False)
    assert s == {"doc_recall": 0.5, "fact_recall": 0.5}
    assert score(item(), "", [], refused=True) == {"doc_recall": 0.0, "fact_recall": 0.0}
    no_numbers = GoldItem(qid="x", question="q", relevant_doc_ids=DOCS, answer_hint="Apply online.")
    assert score(no_numbers, "x", DOCS, refused=False)["fact_recall"] is None


def test_rows_are_appended_and_a_rerun_resumes(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    items = [item("a"), item("b")]
    # quota ends after the first item's two arms (1 one-shot call + 2 agent calls)
    llm = ScriptedLLM("Tuition 6,000 euros [1].", agent_script() * 2, fail_after=3)
    written, stopped = run_comparison(items, settings, FakePipeline(), llm, out)
    assert written == 2 and stopped == "b/oneshot: RuntimeError"
    rows = load_rows(out)
    assert [(r["qid"], r["arm"], r["llm_calls"]) for r in rows] == [("a", "oneshot", 1), ("a", "agent", 2)]
    assert rows[1]["cited_doc_ids"] == DOCS and rows[1]["scores"] == {"doc_recall": 1.0, "fact_recall": 1.0}
    assert rows[1]["steps"] == [{"tool": "search_sources", "args": {"query": "tuition"}, "ok": True}]
    # next day: only item b runs
    llm2 = ScriptedLLM("Tuition 6,000 euros [1].", agent_script())
    written, stopped = run_comparison(items, settings, FakePipeline(), llm2, out)
    assert written == 2 and stopped is None and llm2.calls == 3
    assert [(r["qid"], r["arm"]) for r in load_rows(out)][2:] == [("b", "oneshot"), ("b", "agent")]


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
