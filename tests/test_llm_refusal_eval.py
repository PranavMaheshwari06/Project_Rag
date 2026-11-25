"""LLM-on refusal evaluation: who refused (gate, model, citation check), resumable
rows and the summary, with a fake pipeline and a fake LLM (no network, no key)."""

import pytest

from core.config import load_settings
from evaluation.agent_eval import load_rows
from evaluation.llm_refusal_eval import run_auto_item, run_items, summarize, summarize_auto
from evaluation.retrieval_eval import GoldItem
from generation.prompt_builder import REFUSAL_TEXT
from schemas.common import Chunk, RetrievedChunk


def gold(qid, kind="requirement", expect_refusal=False):
    return GoldItem(qid=qid, question=f"question {qid}?", relevant_doc_ids=[], kind=kind,
                    expect_refusal=expect_refusal)


class Pipeline:
    def __init__(self, score=0.9):
        self.score = score

    def search(self, query, mode="hybrid_rerank", top_k=None, **_):
        c = Chunk(chunk_id="c1", doc_id="d1", source="d1", title="t", section_path="s",
                  url="https://example.org", text="It costs 100 euros.", token_count=5)
        return [RetrievedChunk(chunk=c, rerank_score=self.score)]


class LLM:
    available = True
    model = "m"

    def __init__(self, *replies):
        self.replies = list(replies)

    def complete(self, messages, json_mode=False):
        return self.replies.pop(0)


@pytest.fixture
def settings():
    return load_settings()


def test_each_outcome_is_recorded_and_the_gate_makes_no_llm_call(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    llm = LLM("It costs 100 euros [1].", REFUSAL_TEXT, "It costs money.", "Still money.")
    assert run_items([gold("a"), gold("b"), gold("c")], settings, Pipeline(), llm, out) == (3, None)
    rows = load_rows(out)
    assert [r["outcome"] for r in rows] == ["answered", "llm", "uncited"]
    assert [r["llm_calls"] for r in rows] == [1, 1, 2]  # uncited = the first reply plus the one repair
    gated = tmp_path / "gated.jsonl"
    assert run_items([gold("z")], settings, Pipeline(0.0), LLM(), gated) == (1, None)
    row = load_rows(gated)[0]
    assert row["outcome"] == "gate" and row["llm_calls"] == 0 and row["model"] is None


def test_a_rerun_skips_the_items_already_done(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    run_items([gold("a")], settings, Pipeline(), LLM("Yes [1]."), out)
    assert run_items([gold("a"), gold("b")], settings, Pipeline(), LLM("Yes [1]."), out) == (1, None)
    assert [r["qid"] for r in load_rows(out)] == ["a", "b"]


def test_summary_separates_answerable_from_expected_refusals():
    def row(q, kind, expect, o):
        return {"qid": q, "kind": kind, "expect_refusal": expect, "outcome": o, "model": "m"}

    s = summarize([row("a", "requirement", False, "answered"), row("b", "requirement", False, "llm"),
                   row("c", "country_rules", False, "gate"), row("d", "refusal", True, "llm"),
                   row("e", "coverage", True, "answered")], resamples=50)
    assert s["answerable"]["n"] == 3 and s["answerable"]["refused"] == 2
    assert s["answerable"]["llm"] == 1 and s["answerable"]["gate"] == 1 and s["answerable"]["refusal_rate"] == 0.667
    assert s["expected_refusals"] == {"n": 2, "refused": 1, "answered_anyway": 1}
    assert s["by_kind"]["requirement"]["answered"] == 1


# --- `auto`: the agent's outcome where `auto` would escalate the stored one-shot row ---------------------
SEARCH = '{"tool": "search_sources", "args": {"query": "fee"}}'
FINAL = '{"answer": "It costs 100 euros [1]."}'


class Scores(Pipeline):
    """The first search returns the first score; later searches (the agent's own) pass the gate."""

    def __init__(self, first):
        super().__init__(first)

    def search(self, query, **kw):
        hits = super().search(query, **kw)
        self.score = 0.9
        return hits


def base(qid, outcome, expect=False, kind="requirement", calls=1):
    return {"qid": qid, "kind": kind, "expect_refusal": expect, "outcome": outcome, "answer": "one-shot answer",
            "llm_calls": calls, "latency_ms": 1000, "model": "m"}


@pytest.mark.parametrize("outcome,score,escalates", [
    ("answered", 0.9, False), ("guardrail", 0.9, False), ("gate", 0.001, False),
    ("gate", 0.1, True), ("llm", 0.9, True), ("uncited", 0.9, True),
])
def test_auto_runs_the_agent_only_where_auto_would_escalate(settings, outcome, score, escalates):
    llm = LLM(SEARCH, FINAL)
    item = GoldItem(qid="a", question="fee?", relevant_doc_ids=["d1"])
    row = run_auto_item(item, base("a", outcome), settings, Scores(score), llm)
    assert row["escalated"] is escalates and len(llm.replies) == (0 if escalates else 2)
    if escalates:
        assert row["outcome"] == "answered" and row["cited_doc_ids"] == ["d1"] and row["cites_gold"] is True
    else:
        assert row["outcome"] == outcome and row["answer"] == "one-shot answer"


def test_a_call_cap_stops_a_run_between_items(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    written, stopped = run_items([gold("a"), gold("b")], settings, Pipeline(), LLM("Yes [1]."), out, max_calls=1)
    assert written == 1 and stopped == "call cap of 1 reached"


def test_auto_summary_compares_each_item_with_its_one_shot_row():
    one = [base("a", "answered"), base("b", "llm"), base("c", "gate", calls=0),
           base("d", "llm", True, "refusal"), base("e", "gate", True, "coverage", calls=0),
           base("not-run-yet", "llm")]

    def auto(row, outcome, calls=0, latency=0, cites=None):
        return {**row, "outcome": outcome, "escalated": calls > 0, "llm_calls": calls, "latency_ms": latency,
                "cites_gold": cites}

    s = summarize_auto(one, [auto(one[0], "answered"), auto(one[1], "answered", 4, 40000, True),
                             auto(one[2], "budget", 6, 60000), auto(one[3], "answered", 3, 20000),
                             auto(one[4], "gate")], resamples=50)
    assert s["items"] == 5  # only the items auto has run are compared
    assert (s["one_shot"]["refused"], s["answerable"]["refused"], s["answerable"]["budget"]) == (2, 1, 1)
    assert s["paired"]["to_answered"] == ["b"] and s["paired"]["to_refused"] == []
    assert s["paired"]["sign_test_p"] == 1.0
    assert s["escalated"] == {"answerable": 2, "probes": 1} and s["probes_answered"] == ["d"]
    assert s["new_answers_citing_a_gold_page"] == "1 of 1"
    assert s["calls_per_question"] == {"one_shot": 0.6, "auto": 3.2}
    assert s["escalation_added_latency_ms"] == {"p50": 40000, "p95": 60000}
