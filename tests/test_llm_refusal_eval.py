"""LLM-on refusal evaluation: who refused (gate, model, citation check), resumable
rows and the summary, with a fake pipeline and a fake LLM (no network, no key)."""

import json

import pytest

from core.config import load_settings
from evaluation.agent_eval import load_rows
from evaluation.llm_refusal_eval import run_auto_item, run_items, summarize, summarize_auto
from evaluation.retrieval_eval import GoldItem, load_gold
from generation.prompt_builder import REFUSAL_TEXT
from schemas.common import Chunk, RetrievedChunk
from scripts import llm_refusal


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
        # enough to audit an answer later: what the agent looked up and which passages it cited
        assert row["cited_chunk_ids"] == ["c1"] and row["steps"] == [
            {"tool": "search_sources", "args": {"query": "fee"}, "ok": True, "markers": [1]}]
        assert row["escalation_ms"] >= 0
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
        # latency_ms also holds the harness's own re-retrieval; escalation_ms is the agent alone
        return {**row, "outcome": outcome, "escalated": calls > 0, "llm_calls": calls, "latency_ms": latency + 999,
                "escalation_ms": latency, "cites_gold": cites}

    s = summarize_auto(one, [auto(one[0], "answered"), auto(one[1], "answered", 4, 40000, True),
                             auto(one[2], "budget", 6, 60000), auto(one[3], "answered", 3, 20000),
                             auto(one[4], "gate")], resamples=50)
    assert s["items"] == 5 and s["one_shot_items_not_run"] == 1  # only the items auto has run are compared
    assert (s["one_shot"]["refused"], s["answerable"]["refused"], s["answerable"]["budget"]) == (2, 1, 1)
    assert s["recovered"] == ["b"] and s["recovered_citing_a_gold_page"] == "1 of 1"
    assert "paired" not in s  # auto never turns an answer into a refusal, so a significance test would say nothing
    assert s["by_one_shot_outcome"] == {"gate": {"escalated": 1, "recovered": 0}, "llm": {"escalated": 2, "recovered": 1}}
    assert s["escalated"] == {"answerable": 2, "probes": 1}
    assert s["one_shot"]["probes_answered"] == [] and s["probes_answered"] == s["probes_newly_answered"] == ["d"]
    assert s["one_shot"]["models"] == ["m"]
    assert s["calls_per_question"] == {"one_shot": 0.6, "auto": 3.2}
    assert s["escalation_added_latency_ms"] == {"p50": 40000, "p95": 60000}


def test_auto_rows_that_do_not_match_the_one_shot_rows_are_rejected():
    """A one-shot re-run (new prompt, new corpus) must not be compared with escalations of the old replies."""
    one = {**base("a", "llm"), "run_at": "2026-01-02T00:00:00+00:00"}
    row = {**one, "escalated": True, "cites_gold": None}
    for stale in ({**row, "run_at": "2026-01-01T00:00:00+00:00"},
                  {**row, "escalated": False, "outcome": "answered"}, {**row, "qid": "gone"}):
        with pytest.raises(ValueError, match="delete the auto rows"):
            summarize_auto([one], [stale], resamples=0)


def test_a_crashed_tool_leaves_no_row(settings):
    class Broken(Pipeline):
        def search(self, query, **kw):
            raise MemoryError("reranker")

    with pytest.raises(RuntimeError, match="tool crashed"):
        run_auto_item(gold("a"), base("a", "llm"), settings, Broken(), LLM(SEARCH, json.dumps({"answer": REFUSAL_TEXT})))


def test_the_delay_between_calls_is_not_counted_as_latency(settings, tmp_path):
    out = tmp_path / "rows.jsonl"
    run_items([gold("a"), gold("b")], settings, Pipeline(), LLM("Yes [1].", "Yes [1]."), out, delay_s=0.3)
    rows = load_rows(out)
    assert rows[1]["latency_ms"] < 150 and rows[1]["models"] == ["m"]


def test_auto_summary_only_writes_the_auto_file_and_leaves_one_shot_alone(tmp_path, monkeypatch):
    s = load_settings()
    for field in ("llm_refusal_rows_out", "llm_refusal_out", "auto_refusal_rows_out", "auto_refusal_out"):
        setattr(s.evaluation, field, str(tmp_path / field))
    monkeypatch.setattr(llm_refusal, "get_settings", lambda: s)
    assert llm_refusal.main(["--mode", "auto", "--summary-only"]) == 1  # no one-shot rows to build on
    rows = [json.dumps(base(i.qid, "llm")) for i in load_gold(s.resolve(s.evaluation.gold_path))]
    (tmp_path / "llm_refusal_rows_out").write_text("\n".join(rows) + "\n")
    assert llm_refusal.main(["--mode", "auto", "--summary-only"]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["auto_refusal_out", "llm_refusal_rows_out"]
