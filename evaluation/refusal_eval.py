"""Calibrate the score gate, without generation or repeated model calls.

These are calibration-set measurements, not held-out estimates. Empty retrieval
always refuses; equality with the threshold answers, matching generate_answer.
"""

import math


def gate_refuses(row: dict, threshold: float) -> bool:
    return not row["has_results"] or row["top_score"] < threshold


def confusion(rows: list[dict], predictions: list[bool]) -> dict:
    if len(rows) != len(predictions):
        raise ValueError("one prediction is required for every item")
    tp = fp = tn = fn = 0
    for row, refused in zip(rows, predictions):
        if row["expect_refusal"]:
            tp += int(refused)
            fn += int(not refused)
        else:
            fp += int(refused)
            tn += int(not refused)
    return {
        "true_refusals": tp, "false_refusals": fp,
        "correct_answers": tn, "missed_refusals": fn,
        "answerable_count": tn + fp, "refusal_count": tp + fn,
        "refusal_recall": tp / (tp + fn) if tp + fn else None,
        "refusal_precision": tp / (tp + fp) if tp + fp else None,
        "false_refusal_rate": fp / (tn + fp) if tn + fp else None,
    }


def calibrate(rows: list[dict], configured_threshold: float, max_false_refusal_rate: float = 0.05) -> dict:
    if not 0 <= configured_threshold <= 1 or not 0 <= max_false_refusal_rate <= 1:
        raise ValueError("threshold and false refusal limit must be in [0, 1]")
    candidates = {0.0, 1.0, configured_threshold}
    for row in rows:
        score = row["top_score"]
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("reranker scores must be finite and in [0, 1]")
        candidates.add(score)
        if score < 1:
            candidates.add(math.nextafter(score, 1.0))
    sweep = []
    for threshold in sorted(candidates):
        metrics = confusion(rows, [gate_refuses(r, threshold) for r in rows])
        sweep.append({"threshold": threshold, **metrics})
    both_classes = any(r["expect_refusal"] for r in rows) and any(not r["expect_refusal"] for r in rows)
    feasible = [p for p in sweep if p["false_refusal_rate"] is not None
                and p["false_refusal_rate"] <= max_false_refusal_rate]
    if both_classes and feasible:
        best = min(feasible, key=lambda p: (-p["true_refusals"], p["false_refusals"], p["threshold"]))
        status = "calibrated"
    else:
        best = next(p for p in sweep if p["threshold"] == configured_threshold)
        status = "insufficient_classes" if not both_classes else "constraint_infeasible"
    threshold = best["threshold"]
    per_item = [{**r, "gate_refused": gate_refuses(r, threshold)} for r in rows]
    return {
        "method": "calibration-set score sweep (not held-out evaluation)",
        "status": status, "configured_threshold": configured_threshold,
        "selected_threshold": threshold, "max_false_refusal_rate": max_false_refusal_rate,
        "constraint_met": best["false_refusal_rate"] is not None
        and best["false_refusal_rate"] <= max_false_refusal_rate,
        "selection_rule": "maximize refusal recall; then fewer false refusals; then lower threshold",
        "selected": best,
        "configured": next(p for p in sweep if p["threshold"] == configured_threshold),
        "by_kind": {kind: confusion([r for r in per_item if r["kind"] == kind],
                                    [r["gate_refused"] for r in per_item if r["kind"] == kind])
                    for kind in sorted({r["kind"] for r in rows})},
        "sweep": sweep, "per_item": per_item,
    }
