"""Agent vs one-shot RAG on the multi_hop gold items. Each (item, arm) result is
appended to a JSONL file as soon as both arms of the item are done, so a run
stopped by the daily quota resumes where it stopped. The two rows of an item are
written together, and only when one model answered every call of both arms
(LLMClient switches model on a 429); a mixed pair is dropped and retried later.

Scores are deterministic, no LLM judge:
- doc_recall: share of the item's relevant_doc_ids among the documents the
  answer cites (a multi-hop answer needs every hop's page).
- fact_recall: share of the numbers in the reviewed answer_hint that appear in
  the answer (amounts, dates, durations); None when the hint has no number.
A refusal, or an answer with no valid citation, scores 0 on both, in both arms.
Citation markers are removed before numbers are read. The headline is the paired difference agent minus
one-shot with a bootstrap interval: above zero is a win, containing zero is noise."""

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from agent.loop import run_agent
from agent.tools import Toolbox
from core.config import Settings
from evaluation.bootstrap import bootstrap_ci
from evaluation.retrieval_eval import GoldItem
from generation.answer_generator import generate_answer
from generation.citation_mapper import CITE_RE, map_citations
from generation.llm_client import is_provider_error

log = logging.getLogger(__name__)

ARMS = ("oneshot", "agent")
METRICS = ("doc_recall", "fact_recall")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text: str) -> set[str]:
    """Numbers with thousands separators dropped, a decimal comma read as a point and
    trailing decimal zeros cut: "11,904" and "11.904" -> "11904", "2,5" -> "2.5",
    "361,00" -> "361". [n] citation markers are not numbers of the answer."""
    out = set()
    for n in NUMBER_RE.findall(CITE_RE.sub("", text)):
        n = re.sub(r"[.,](?=\d{3}(?!\d))", "", n).replace(",", ".")  # ponytail: "1.500" is 1500, never 1.5
        out.add(n.rstrip("0").rstrip(".") if "." in n else n)
    return out


def score(item: GoldItem, answer: str, cited_doc_ids: list[str], refused: bool) -> dict:
    hint = numbers(item.answer_hint)
    if refused:
        return {"doc_recall": 0.0, "fact_recall": 0.0 if hint else None}
    relevant = set(item.relevant_doc_ids)
    return {
        "doc_recall": round(len(relevant & set(cited_doc_ids)) / len(relevant), 3) if relevant else None,
        "fact_recall": round(len(hint & numbers(answer)) / len(hint), 3) if hint else None,
    }


def run_oneshot(item: GoldItem, settings: Settings, pipeline, llm) -> dict:
    retrieved = pipeline.search(item.question, mode="hybrid_rerank", top_k=settings.retrieval.final_top_k)
    draft = generate_answer(item.question, retrieved, settings, llm)
    text, citations = map_citations(draft.text, draft.evidence)
    # an uncited answer counts as a refusal, as it does in the agent arm
    return {"answer": text, "refused": draft.refused or not citations, "stop": draft.mode,
            "cited_doc_ids": [draft.evidence[c.marker - 1].doc_id for c in citations], "steps": []}


def run_agent_arm(item: GoldItem, settings: Settings, pipeline, llm) -> dict:
    out = run_agent(item.question, Toolbox(settings, pipeline), llm)  # no profile: gold items carry none
    return {"answer": out.text, "refused": out.refused, "stop": out.stop_reason,
            "cited_doc_ids": [out.evidence[c.marker - 1].doc_id for c in out.citations],
            "steps": [{"tool": s.tool, "args": s.args, "ok": s.ok} for s in out.steps]}


RUNNERS = {"oneshot": run_oneshot, "agent": run_agent_arm}


class Metered:
    """Counts LLM calls and spaces them `delay_s` apart: a burst of agent steps would
    otherwise hit the per-minute limit, and LLMClient treats any 429 as quota used up."""

    def __init__(self, llm, delay_s: float = 0.0):
        self.llm, self.delay_s, self.calls, self._last = llm, delay_s, 0, 0.0
        self.answered_by: list[str | None] = []  # the model that answered each successful call

    @property
    def available(self) -> bool:
        return self.llm.available

    @property
    def model(self) -> str | None:
        return getattr(self.llm, "model", None)

    def complete(self, messages: list[dict], json_mode: bool = False) -> str:
        time.sleep(max(0.0, self._last + self.delay_s - time.monotonic()))
        try:
            reply = self.llm.complete(messages, json_mode=json_mode)
            self.answered_by.append(self.model)  # after the call: a 429 switch happens inside it
            return reply
        finally:
            self.calls += 1
            self._last = time.monotonic()


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            rows.append(json.loads(line)) if line.strip() else None
        except json.JSONDecodeError:  # a line torn by a crash mid-write: its pair re-runs
            log.warning("skipping unreadable line %d of %s", n, path.name)
    return rows


def run_comparison(items: list[GoldItem], settings: Settings, pipeline, llm, out: Path,
                   limit: int | None = None, delay_s: float = 0.0) -> tuple[int, str | None, int]:
    """Run the items that lack a complete pair. Returns the rows written, why the run
    stopped early (a provider error: quota, overload) or None, and how many pairs were
    dropped because the model changed inside them. Any other exception is a bug and raises."""
    arms: dict[str, set[str]] = {}
    for r in load_rows(out):
        arms.setdefault(r["qid"], set()).add(r["arm"])
    done = {q for q, a in arms.items() if a >= set(ARMS)}
    todo = [i for i in items if i.qid not in done][:limit]
    out.parent.mkdir(parents=True, exist_ok=True)
    llm = Metered(llm, delay_s)
    written = mixed = 0
    for item in todo:
        pair, models = [], set()
        for arm in ARMS:
            t0, calls, answered = time.perf_counter(), llm.calls, len(llm.answered_by)
            try:
                result = RUNNERS[arm](item, settings, pipeline, llm)
            except Exception as e:
                if not is_provider_error(e):
                    raise
                return written, f"{item.qid}/{arm}: {type(e).__name__}", mixed
            models |= set(llm.answered_by[answered:])
            pair.append({"qid": item.qid, "arm": arm, "llm_calls": llm.calls - calls,
                         "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "latency_ms": round((time.perf_counter() - t0) * 1000), **result,
                         "scores": score(item, result["answer"], result["cited_doc_ids"], result["refused"])})
        if len(models) > 1:  # not a like-for-like pair: drop it, the next run repeats the item
            log.warning("%s: model changed inside the pair (%s); dropped", item.qid, sorted(models))
            mixed += 1
            continue
        model = next(iter(models), None)
        with out.open("a", encoding="utf-8") as fh:
            fh.write("".join(json.dumps({"model": model, **row}, ensure_ascii=False) + "\n" for row in pair))
        written += len(pair)
    return written, None, mixed


def summarize(rows: list[dict], items: list[GoldItem], resamples: int = 2000, seed: int = 0) -> dict:
    by = {(r["qid"], r["arm"]): r for r in rows}  # a re-run row for the same pair wins
    qids = [i.qid for i in items if all((i.qid, a) in by for a in ARMS)]
    summary = {"items_total": len(items), "items_paired": len(qids), "method": "deterministic: cited-doc "
               "recall and hint-number recall; paired bootstrap on agent minus one-shot", "metrics": {}}
    for m in METRICS:
        pairs = [(by[q, "agent"]["scores"][m], by[q, "oneshot"]["scores"][m]) for q in qids
                 if by[q, "agent"]["scores"][m] is not None and by[q, "oneshot"]["scores"][m] is not None]
        diffs = [a - o for a, o in pairs]
        summary["metrics"][m] = {
            "n": len(pairs),
            "agent": round(sum(a for a, _ in pairs) / len(pairs), 3) if pairs else None,
            "oneshot": round(sum(o for _, o in pairs) / len(pairs), 3) if pairs else None,
            "diff": round(sum(diffs) / len(diffs), 3) if diffs else None,
            "diff_ci": bootstrap_ci(diffs, resamples, seed) if diffs else None,
        }
    for arm in ARMS:
        arm_rows = [by[q, arm] for q in qids]
        summary[arm] = {
            "refused": sum(r["refused"] for r in arm_rows),
            "llm_calls_mean": round(sum(r["llm_calls"] for r in arm_rows) / len(arm_rows), 2) if arm_rows else None,
            "models": sorted({r["model"] or "-" for r in arm_rows}),
        }
    return summary
