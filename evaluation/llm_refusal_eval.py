"""End-to-end refusal rate of one-shot RAG with the LLM switched on. The Phase 4
calibration ran without a key (extractive fallback), so it measures only the score
gate; the model can also refuse on its own, and in the agent comparison it did so on
21 of 28 multi-hop questions. This runs the real one-shot path on every gold item
except the multi-hop ones and splits each outcome by who refused:

- gate: the best rerank score was under the threshold, no LLM call was made
- llm: the gate passed and the model answered with the refusal text
- uncited: no valid [n] marker even after the one repair call (the answer contract refuses it)
- guardrail: the answer repeated the system prompt
- answered: a cited answer

Rows are appended as they finish, so a run stopped by quota resumes. Scoring is the
refusal outcome only: whether the answer is right is not judged here.

`auto` mode is measured on top of those rows: each keeps its one-shot outcome unless `auto` would escalate it
(agent.loop.should_escalate), and then the agent runs and its outcome counts. So the two modes are compared on the
same one-shot replies, and the difference is the escalation alone."""

import json
import logging
import time
from collections.abc import Callable
from datetime import date, datetime, timezone
from math import comb
from pathlib import Path

from agent.loop import run_agent, should_escalate
from agent.tools import Toolbox
from core.config import Settings
from core.metrics import percentile
from evaluation.agent_eval import Metered, load_rows
from evaluation.bootstrap import bootstrap_ci
from evaluation.retrieval_eval import GoldItem
from generation.answer_generator import generate_answer
from generation.llm_client import is_provider_error

log = logging.getLogger(__name__)
OUTCOMES = ("gate", "llm", "uncited", "guardrail", "answered")
AUTO_OUTCOMES = (*OUTCOMES, "budget", "bad_output")  # the agent's two extra ways to give up


# the draft's refusal_reason, under the labels the committed results already use
OUTCOME = {None: "answered", "gate": "gate", "model": "llm", "uncited": "uncited", "guardrail": "guardrail"}
REASON = {label: reason for reason, label in OUTCOME.items()}
AGENT_OUTCOME = {**{label: label for label in AUTO_OUTCOMES}, "refused": "llm"}  # the agent's stop reasons


def run_item(item: GoldItem, settings: Settings, pipeline, llm) -> dict:
    retrieved = pipeline.search(item.question, mode="hybrid_rerank", top_k=settings.retrieval.final_top_k)
    draft = generate_answer(item.question, retrieved, settings, llm)
    return {"outcome": OUTCOME[draft.refusal_reason], "answer": draft.text[:400]}


def run_auto_item(item: GoldItem, base: dict, settings: Settings, pipeline, llm) -> dict:
    """`auto` on one item, given its stored one-shot row."""
    reason, top = REASON[base["outcome"]], 0.0
    if reason == "gate":  # the row keeps no score; retrieval is deterministic, so ask again (no LLM call)
        hits = pipeline.search(item.question, mode="hybrid_rerank", top_k=settings.retrieval.final_top_k)
        top = (hits[0].rerank_score or 0.0) if hits else 0.0
    if not should_escalate(reason, top, settings.agent.escalate_min_score):
        return {"escalated": False, "outcome": base["outcome"], "answer": base["answer"], "cites_gold": None}
    out = run_agent(item.question, Toolbox(settings, pipeline, as_of=date.today()), llm)
    cited = sorted({out.evidence[c.marker - 1].doc_id for c in out.citations})
    gold = set(item.relevant_doc_ids)
    return {"escalated": True, "outcome": AGENT_OUTCOME[out.stop_reason], "answer": out.text[:1500],
            "cited_doc_ids": cited, "cites_gold": bool(gold & set(cited)) if gold and not out.refused else None}


def run_items(items: list[GoldItem], settings: Settings, pipeline, llm, out: Path,
              limit: int | None = None, delay_s: float = 0.0, run: Callable[..., dict] | None = None,
              max_calls: int | None = None) -> tuple[int, str | None]:
    """Run the items without a row yet. Returns (rows written, why it stopped early or None).
    A provider error (quota, overload) stops cleanly; any other exception is a bug and raises.
    `max_calls` stops the run before the next item once that many LLM calls were made."""
    done = {r["qid"] for r in load_rows(out)}
    todo = [i for i in items if i.qid not in done][:limit]
    out.parent.mkdir(parents=True, exist_ok=True)
    llm, written = Metered(llm, delay_s), 0
    for item in todo:
        if max_calls is not None and llm.calls >= max_calls:
            return written, f"call cap of {max_calls} reached"
        calls, t0 = llm.calls, time.perf_counter()
        try:
            result = (run or run_item)(item, settings, pipeline, llm)
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


def summarize(rows: list[dict], resamples: int = 2000, seed: int = 0, outcomes: tuple[str, ...] = OUTCOMES) -> dict:
    by = {r["qid"]: r for r in rows}.values()  # a re-run row for the same item wins
    summary: dict = {"items": len(by), "method": "refusal outcome of the real one-shot path with the LLM on; "
                     "answer correctness is not judged", "by_kind": {}}
    for kind in sorted({r["kind"] for r in by}):
        rs = [r for r in by if r["kind"] == kind]
        summary["by_kind"][kind] = {"n": len(rs), **{o: sum(r["outcome"] == o for r in rs) for o in outcomes}}
    answerable = [r for r in by if not r["expect_refusal"]]
    expected = [r for r in by if r["expect_refusal"]]
    flags = [float(r["outcome"] != "answered") for r in answerable]
    summary["answerable"] = {"n": len(answerable), "refused": int(sum(flags)),
                             **{o: sum(r["outcome"] == o for r in answerable) for o in outcomes},
                             "refusal_rate": round(sum(flags) / len(flags), 3) if flags else None,
                             "refusal_rate_ci": bootstrap_ci(flags, resamples, seed) if flags else None}
    summary["expected_refusals"] = {"n": len(expected),
                                    "refused": sum(r["outcome"] != "answered" for r in expected),
                                    "answered_anyway": sum(r["outcome"] == "answered" for r in expected)}
    summary["models"] = sorted({r["model"] or "-" for r in by})
    return summary


def summarize_auto(base_rows: list[dict], auto_rows: list[dict], resamples: int = 2000, seed: int = 0) -> dict:
    """The refusal table for `auto`, and its paired comparison with one-shot on the items `auto` has run."""
    auto = {r["qid"]: r for r in auto_rows}
    base = {r["qid"]: r for r in base_rows if r["qid"] in auto}
    summary = summarize(list(auto.values()), resamples, seed, AUTO_OUTCOMES)
    summary["method"] = ("`auto` on top of the stored one-shot rows (llm_refusal.jsonl): the one-shot outcome "
                         "stands unless `auto` escalates it, then the agent's outcome counts. Answer correctness "
                         "is not judged.")

    def refused(row: dict) -> bool:
        return row["outcome"] != "answered"

    answerable = [q for q, r in auto.items() if not r["expect_refusal"]]
    one = summarize(list(base.values()), resamples, seed)["answerable"]
    summary["one_shot"] = {k: one[k] for k in ("refused", "refusal_rate", "refusal_rate_ci")}
    to_answered = sorted(q for q in answerable if refused(base[q]) and not refused(auto[q]))
    to_refused = sorted(q for q in answerable if not refused(base[q]) and refused(auto[q]))
    n, k = len(to_answered) + len(to_refused), min(len(to_answered), len(to_refused))
    diffs = [float(refused(auto[q])) - float(refused(base[q])) for q in answerable]
    summary["paired"] = {"to_answered": to_answered, "to_refused": to_refused,
                         "sign_test_p": round(min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n), 4),
                         "refusal_rate_diff_ci": bootstrap_ci(diffs, resamples, seed) if diffs else None}
    escalated = [r for r in auto.values() if r["escalated"]]
    summary["escalated"] = {"answerable": sum(not r["expect_refusal"] for r in escalated),
                            "probes": sum(r["expect_refusal"] for r in escalated)}
    summary["probes_answered"] = sorted(q for q, r in auto.items() if r["expect_refusal"] and not refused(r))
    cited = sum(auto[q]["cites_gold"] is True for q in to_answered)
    summary["new_answers_citing_a_gold_page"] = f"{cited} of {len(to_answered)}"
    one_calls = sum(r["llm_calls"] for r in base.values())
    total = len(auto) or 1
    summary["calls_per_question"] = {
        "one_shot": round(one_calls / total, 2),
        "auto": round((one_calls + sum(r["llm_calls"] for r in auto.values())) / total, 2)}
    added = [r["latency_ms"] for r in escalated]
    summary["escalation_added_latency_ms"] = {"p50": percentile(added, 50), "p95": percentile(added, 95)}
    return summary
