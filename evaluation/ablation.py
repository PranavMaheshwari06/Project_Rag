"""Phase 5 ablation on hybrid+rerank: no filter (baseline), oracle filters from
the gold metadata (upper bound) and the rule-based detector (what a deployed
system can do). An arm counts as a win only if the paired bootstrap interval of
its per-query MRR gain over the baseline lies above zero. Refusal behaviour is
reported per arm too: a filter changes the top rerank score the refusal gate reads."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from core.config import Settings
from evaluation.bootstrap import bootstrap_ci
from evaluation.retrieval_eval import GoldItem, count_relevant_chunks, evaluate_ranking, load_gold
from evaluation.runner import aggregate
from retrieval.filters import detect_filters
from retrieval.pipeline import build_pipeline

ARMS = ("baseline", "oracle_filter", "detected_filter")
MODE = "hybrid_rerank"


def arm_filters(arm: str, item: GoldItem) -> dict[str, list[str]] | None:
    if arm == "oracle_filter":
        scope = {"university": item.university, "programme": item.programme}
        return {k: [v] for k, v in scope.items() if v} or None
    if arm == "detected_filter":
        return detect_filters(item.question) or None
    return None


def _gain(rows: list[dict], base: list[dict], metric, boot: tuple[int, int]) -> dict:
    diffs = [metric(r) - metric(b) for r, b in zip(rows, base)]
    return {"mean": round(sum(diffs) / len(diffs), 3) if diffs else 0.0, "ci": bootstrap_ci(diffs, *boot)}


def run_ablation(settings: Settings) -> dict:
    pipeline = build_pipeline(settings)
    gold = load_gold(settings.resolve(settings.evaluation.gold_path))
    ks, k5 = settings.evaluation.k_values, f"@{settings.evaluation.k_values[0]}"
    threshold = settings.generation.refusal_threshold
    corpus = list(pipeline.chunks.values())
    pipeline.search(gold[0].question, mode=MODE, top_k=max(ks))  # warm models before timing
    rows = {arm: [] for arm in ARMS}
    for item in gold:
        total = count_relevant_chunks(corpus, item) if item.relevant_doc_ids else 0
        for arm in ARMS:
            filters = arm_filters(arm, item)
            start = time.perf_counter()
            ranked = pipeline.search(item.question, mode=MODE, top_k=max(ks), filters=filters)
            row = {"qid": item.qid, "kind": item.kind, "reviewed_by": item.reviewed_by, "filters": filters,
                   "latency_ms": (time.perf_counter() - start) * 1000,
                   "refused": not ranked or (ranked[0].rerank_score or 0.0) < threshold}
            if item.relevant_doc_ids:
                row["metrics"] = evaluate_ranking([r.chunk for r in ranked], item, ks, total)
            rows[arm].append(row)

    boot = (settings.evaluation.bootstrap_resamples, settings.evaluation.bootstrap_seed)
    kinds = sorted({g.kind for g in gold if g.relevant_doc_ids})
    groups = {"all": lambda r: True, "human_reviewed": lambda r: r["reviewed_by"] == "human"}
    groups |= {k: (lambda r, k=k: r["kind"] == k) for k in kinds}
    summary = {}
    for group, keep in groups.items():
        pick = lambda rs: [r for r in rs if "metrics" in r and keep(r)]  # noqa: E731
        base = pick(rows["baseline"])
        summary[group] = {}
        for arm in ARMS:
            arm_rows = pick(rows[arm])
            entry = aggregate(arm, arm_rows, ks, *boot).model_dump()
            if arm != "baseline":
                entry["mrr_gain"] = _gain(arm_rows, base, lambda r: r["metrics"]["rr"], boot)
                entry[f"recall{k5}_gain"] = _gain(arm_rows, base, lambda r: r["metrics"]["recall"][k5], boot)
                entry["wins"] = entry["mrr_gain"]["ci"][0] > 0
            summary[group][arm] = entry
    refusal = {arm: {"probes": sum(1 for r in rs if "metrics" not in r),
                     "probes_refused": sum(r["refused"] for r in rs if "metrics" not in r),
                     "answerable": sum(1 for r in rs if "metrics" in r),
                     "answerable_refused": sum(r["refused"] for r in rs if "metrics" in r)}
               for arm, rs in rows.items()}
    return {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "mode": MODE,
            "refusal_threshold": threshold, "bootstrap_resamples": boot[0], "bootstrap_seed": boot[1],
            "gold_items": len(gold), "chunk_count": len(corpus),
            "reviewer_counts": {w: sum(g.reviewed_by == w for g in gold) for w in ("human", "model")},
            "summary": summary, "refusal": refusal, "per_query": rows}


def render_markdown(result: dict) -> str:
    lines = ["| questions | arm | n | MRR [95% CI] | MRR gain vs baseline [95% CI] | Recall@5 | p50 ms |",
             "|---|---|---|---|---|---|---|"]
    for group, arms in result["summary"].items():
        for arm, m in arms.items():
            mrr = f"{m['mrr']:.3f} [{m['mrr_ci'][0]:.3f}, {m['mrr_ci'][1]:.3f}]" if m["mrr_ci"] else f"{m['mrr']:.3f}"
            gain = "—"
            if "mrr_gain" in m:
                g = m["mrr_gain"]
                gain = f"{g['mean']:+.3f} [{g['ci'][0]:+.3f}, {g['ci'][1]:+.3f}]" + (" **win**" if m["wins"] else "")
            lines.append(f"| {group} | {arm} | {m['query_count']} | {mrr} | {gain} | "
                         f"{m['recall']['@5']:.3f} | {m['latency_p50_ms']:.0f} |")
    lines += ["", "| arm | refusal probes refused | answerable questions refused |", "|---|---|---|"]
    for arm, r in result["refusal"].items():
        lines.append(f"| {arm} | {r['probes_refused']}/{r['probes']} | {r['answerable_refused']}/{r['answerable']} |")
    return "\n".join(lines)


def write(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
