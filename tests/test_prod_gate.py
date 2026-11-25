"""The CI eval gate: a number under its floor, a missing number, a rule that checks nothing and numbers computed
on other inputs all fail."""

import hashlib
import json

import pytest

from core.config import load_settings
from scripts import check_gate

DOC = {"recall": {"@5": 0.8}, "refused": 13, "ok": True, "none": None, "ci": [0.4, 0.8],
       "configs": [{"name": "vector", "mrr": 0.1}, {"name": "hybrid_rerank", "mrr": 0.7}]}


def check(rules):
    return check_gate.failures(DOC, rules, "f.json", load_settings())


def test_numbers_inside_their_bounds_pass():
    assert check({"recall.@5": {"min": 0.77}, "refused": {"min": 13, "max": 13}, "ok": {"equals": True},
                  "configs.hybrid_rerank.mrr": {"min": 0.7}, "ci.0": {"min": 0.0}}) == []


def test_a_number_outside_its_bound_is_named():
    assert check({"recall.@5": {"min": 0.81}, "refused": {"max": 12}}) == [
        "f.json: recall.@5 = 0.8, required min 0.81",
        "f.json: refused = 13, required max 12",
    ]


@pytest.mark.parametrize("path, rule", [
    ("absent", {"min": 1}),
    ("configs.bm25.mrr", {"min": 0}),
    ("ci.5", {"min": 0}),
    ("recall.@5.deeper", {"min": 0}),
    ("none", {"min": 0}),
    ("ok", {"min": 0}),  # a boolean is not a number
    ("ok", {"equals": False}),
    ("refused", {}),  # a rule that checks nothing
    ("refused", {"mim": 1}),  # a typo
])
def test_anything_the_gate_cannot_check_fails(path, rule):
    assert len(check({path: rule})) == 1


def test_a_result_computed_on_other_inputs_fails(tmp_path):
    gold = tmp_path / "gold.jsonl"
    gold.write_text("old")
    doc = {"hash": hashlib.sha256(b"old").hexdigest(), "threshold": 0.5}
    rules = {"hash": {"sha256_of": str(gold)}, "threshold": {"equals_setting": "generation.refusal_threshold"}}
    settings = load_settings()
    settings.generation.refusal_threshold = 0.5
    assert check_gate.failures(doc, rules, "f.json", settings) == []
    gold.write_text("new")
    settings.generation.refusal_threshold = 0.6
    assert len(check_gate.failures(doc, rules, "f.json", settings)) == 2
    assert len(check_gate.failures(doc, {"hash": {"sha256_of": str(tmp_path / "gone")}}, "f.json", settings)) == 1


def floors(tmp_path, content):
    path = tmp_path / "floors.json"
    path.write_text(json.dumps(content))
    return path


def test_a_missing_result_file_fails(tmp_path):
    path = floors(tmp_path, {str(tmp_path / "gone.json"): {"a": {"min": 0}}})
    failed, _ = check_gate.run(load_settings(), path)
    assert len(failed) == 1 and "gone.json" in failed[0]


@pytest.mark.parametrize("content", [{}, {"_note": "only a note"}])
def test_a_floors_file_without_checks_is_not_a_pass(tmp_path, content):
    failed, checked = check_gate.run(load_settings(), floors(tmp_path, content))
    assert checked == 0 and failed


def test_a_source_that_lost_its_checks_fails(tmp_path):
    path = floors(tmp_path, {check_gate.LIVE: {}, "frontend/public/benchmark.json": {"gold_size": {"min": 1}}})
    failed, _ = check_gate.run(load_settings(), path)
    assert failed == [f"{check_gate.LIVE}: no checks listed"]


def test_invalid_eligibility_cases_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(check_gate, "validate_cases", lambda cases, settings: ["case x: broken"])
    path = floors(tmp_path, {check_gate.LIVE: {"metrics.cases": {"min": 1}}})
    failed, _ = check_gate.run(load_settings(), path)
    assert len(failed) == 1 and "case x: broken" in failed[0]


def test_the_committed_floors_keep_every_source_and_a_perfect_eligibility_bar():
    committed = json.loads(load_settings().resolve(check_gate.FLOORS).read_text(encoding="utf-8"))
    assert {k for k in committed if not k.startswith("_")} == {
        check_gate.LIVE, "frontend/public/benchmark.json", "evaluation/results/refusal_calibration.json",
        "evaluation/results/agent_comparison.json", "evaluation/results/llm_refusal.json"}
    live = committed[check_gate.LIVE]
    assert live["metrics.headline_agreement.rate"] == live["metrics.criterion_agreement.rate"] == {"min": 1.0}
    assert live["metrics.false_positive_headlines"] == {"max": 0}
    assert live["metrics.cases"]["min"] >= 40 and live["metrics.criterion_agreement.total"]["min"] >= 213


def test_the_eligibility_cases_are_run_live(tmp_path):
    ok = {check_gate.LIVE: {"metrics.cases": {"min": 40}, "metrics.false_positive_headlines": {"max": 0}}}
    assert check_gate.run(load_settings(), floors(tmp_path, ok)) == ([], 2)
    too_high = {check_gate.LIVE: {"metrics.cases": {"min": 10_000}}}
    assert check_gate.main(["--floors", str(floors(tmp_path, too_high))]) == 1
