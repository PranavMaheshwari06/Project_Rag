import math

import pytest

from evaluation.refusal_eval import calibrate, confusion, gate_refuses


def row(qid, score, expected=False, has_results=True):
    return {"qid": qid, "kind": "refusal" if expected else "requirement", "top_score": score,
            "has_results": has_results, "expect_refusal": expected}


def test_gate_matches_strict_threshold_and_empty_results():
    assert not gate_refuses(row("a", 0.3), 0.3)
    assert gate_refuses(row("a", 0.3), math.nextafter(0.3, 1.0))
    assert gate_refuses(row("a", 0, has_results=False), 0)


def test_maximizes_recall_under_false_refusal_budget_with_deterministic_ties():
    rows = [row(str(i), 0.8) for i in range(20)] + [row("low", 0.2), row("r1", 0.1, True), row("r2", 0.4, True)]
    result = calibrate(rows, 0.3)
    assert result["selected"]["true_refusals"] == 2
    assert result["selected"]["false_refusals"] == 1
    assert result["selected_threshold"] == math.nextafter(0.4, 1.0)
    assert result["constraint_met"]
    assert len(result["per_item"]) == len(rows)


def test_equal_scores_cannot_be_separated_and_fewer_false_refusals_win():
    result = calibrate([row("a", 0.5), row("r", 0.5, True)], 0.3)
    assert result["selected"]["true_refusals"] == 0
    assert result["selected"]["false_refusals"] == 0
    assert result["selected_threshold"] == 0


def test_infeasible_constraint_and_missing_class_are_explicit():
    result = calibrate([row("a", 0, has_results=False), row("r", 0.1, True)], 0.3)
    assert result["status"] == "constraint_infeasible"
    assert not result["constraint_met"]
    assert result["selected_threshold"] == 0.3
    assert calibrate([row("a", 0.8)], 0.3)["status"] == "insufficient_classes"
    assert calibrate([], 0.3)["status"] == "insufficient_classes"


def test_score_one_and_zero_and_invalid_scores():
    result = calibrate([row("a", 1), row("r", 0, True)], 0.3)
    assert result["selected"]["true_refusals"] == 1
    assert result["selected"]["false_refusals"] == 0
    for score in (float("nan"), float("inf"), -0.1, 1.1):
        with pytest.raises(ValueError):
            calibrate([row("bad", score)], 0.3)
    with pytest.raises(ValueError):
        confusion([row("a", 0.5)], [])
