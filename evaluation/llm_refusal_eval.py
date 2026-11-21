"""End-to-end refusal rate of one-shot RAG with the LLM switched on. The Phase 4
calibration ran without a key (extractive fallback), so it measures only the score
gate; the model can also refuse on its own, and in the agent comparison it did so on
21 of 28 multi-hop questions. This runs the real one-shot path on every gold item
except the multi-hop ones and splits each outcome by who refused:

- gate: the best rerank score was under the threshold, no LLM call was made
- llm: the gate passed and the model answered with the refusal text
- uncited: an answer with no valid [n] marker (counts as a refusal, as everywhere else)
- answered: a cited answer

Rows are appended as they finish, so a run stopped by quota resumes. Scoring is the
refusal outcome only: whether the answer is right is not judged here."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from core.config import Settings
from evaluation.agent_eval import Metered, load_rows
from evaluation.bootstrap import bootstrap_ci
from evaluation.retrieval_eval import GoldItem
from generation.answer_generator import generate_answer
from generation.citation_mapper import map_citations
from generation.llm_client import is_provider_error

log = logging.getLogger(__name__)
OUTCOMES = ("gate", "llm", "uncited", "answered")


def outcome(gate: bool, refused: bool, cited: bool) -> str:
    if gate:
        return "gate"
    if refused:
        return "llm"
    return "answered" if cited else "uncited"


def run_item(item: GoldItem, settings: Settings, pipeline, llm) -> dict:
    retrieved = pipeline.search(item.question, mode="hybrid_rerank", top_k=settings.retrieval.final_top_k)
    gate = not retrieved or (retrieved[0].rerank_score or 0.0) < settings.generation.refusal_threshold
    draft = generate_answer(item.question, retrieved, settings, llm)
    cited = bool(map_citations(draft.text, draft.evidence)[1]) if not draft.refused else False
    return {"outcome": outcome(gate, draft.refused, cited), "answer": draft.text[:400]}


def run_items(items: list[GoldItem], settings: Settings, pipeline, llm, out: Path,
              limit: int | None = None, delay_s: float = 0.0) -> tuple[int, str | None]:
    """Run the items without a row yet. Returns (rows written, why it stopped early or None).
    A provider error (quota, overload) stops cleanly; any other exception is a bug and raises."""
    done = {r["qid"] for r in load_rows(out)}
    todo = [i for i in items if i.qid not in done][:limit]
    out.parent.mkdir(parents=True, exist_ok=True)
    llm, written = Metered(llm, delay_s), 0
    for item in todo:
        calls, t0 = llm.calls, time.perf_counter()
        try:
            result = run_item(item, settings, pipeline, llm)
        except Exception as e:
            if not is_provider_error(e):
                raise
            return written, f"{item.qid}: {type(e).__name__}"
        row = {"qid": item.qid, "kind": item.kind, "expect_refusal": item.expect_refusal,
               "model": llm.model if llm.calls > calls else None, "llm_calls": llm.calls - calls,
               "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "latency_ms": round((time.perf_counter() - t0) * 1000), **result}
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        written += 1
    return written, None


def summarize(rows: list[dict], resamples: int = 2000, seed: int = 0) -> dict:
    by = {r["qid"]: r for r in rows}.values()  # a re-run row for the same item wins
    summary: dict = {"items": len(by), "method": "refusal outcome of the real one-shot path with the LLM on; "
                     "answer correctness is not judged", "by_kind": {}}
    for kind in sorted({r["kind"] for r in by}):
        rs = [r for r in by if r["kind"] == kind]
        summary["by_kind"][kind] = {"n": len(rs), **{o: sum(r["outcome"] == o for r in rs) for o in OUTCOMES}}
    answerable = [r for r in by if not r["expect_refusal"]]
    expected = [r for r in by if r["expect_refusal"]]
    flags = [float(r["outcome"] != "answered") for r in answerable]
    summary["answerable"] = {"n": len(answerable), "refused": int(sum(flags)),
                             **{o: sum(r["outcome"] == o for r in answerable) for o in OUTCOMES},
                             "refusal_rate": round(sum(flags) / len(flags), 3) if flags else None,
                             "refusal_rate_ci": bootstrap_ci(flags, resamples, seed) if flags else None}
    summary["expected_refusals"] = {"n": len(expected),
                                    "refused": sum(r["outcome"] != "answered" for r in expected),
                                    "answered_anyway": sum(r["outcome"] == "answered" for r in expected)}
    summary["models"] = sorted({r["model"] or "-" for r in by})
    return summary
