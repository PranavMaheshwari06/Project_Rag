"""LLM-on refusal evaluation: who refused (gate, model, citation check), resumable
rows and the summary, with a fake pipeline and a fake LLM (no network, no key)."""

import pytest

from core.config import load_settings
from evaluation.agent_eval import load_rows
from evaluation.llm_refusal_eval import run_items, summarize
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
