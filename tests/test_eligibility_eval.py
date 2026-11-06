"""Eligibility evaluation harness: dataset schema, validator, runner, metrics.

Every case and rule here is a tiny synthetic fixture made up for the harness;
none is a label for a real programme."""

import json
from datetime import date

import pytest
from pydantic import ValidationError

from core.config import load_settings
from eligibility.rules import record_hash
from evaluation.eligibility_dataset import EligibilityCase, load_cases, validate_cases
from evaluation.eligibility_eval import run_cases, write_results

CITE = {"doc_id": "de/x/y", "quote": "at least 120 credits"}
RECORD = {"degree": {"status": "stated", "value": "x", "quote": "at least 120 credits", "doc_id": "de/x/y"}}
RULES = {
    "slug": "fixture-msc",
    "record_sha256": record_hash(RECORD),
    "rules": [
        {"id": "credits", "label": "credits", "check": {"type": "min", "fact": "total_credits", "value": "120"},
         "citations": [CITE], "reviewed_by": "human"},
        {"id": "board", "label": "board", "severity": "info",
         "check": {"type": "university_review", "note": "the board decides"}, "citations": [CITE], "reviewed_by": "human"},
    ],
}


@pytest.fixture
def settings(tmp_path):
    s = load_settings()
    rules_dir, verified_dir = tmp_path / "rules", tmp_path / "verified"
    rules_dir.mkdir()
    verified_dir.mkdir()
    (rules_dir / "fixture-msc.json").write_text(json.dumps(RULES))
    (verified_dir / "fixture-msc.json").write_text(json.dumps({"tier": "human", "record": RECORD}))
    s.paths.rules_dir, s.paths.verified_dir = str(rules_dir), str(verified_dir)
    return s


def case(case_id="C01", credits="120", headline="meets_checked_published_requirements", verdict="meets", **extra):
    base = {
        "case_id": case_id,
        "profile": {"total_credits": credits},
        "slug": "fixture-msc",
        "intake": "winter",
        "starting_year": 2027,
        "as_of": "2027-03-01",
        "expected_headline": headline,
        "expected_criteria": [{"rule_id": "credits", "verdict": verdict, "citations": [CITE]}],
        "rationale": "synthetic harness fixture",
        "citations": [CITE],
        "author": "assisted",
        "reviewer": None,
    }
    return EligibilityCase.model_validate({**base, **extra})


# --- schema and validator --------------------------------------------------------
def test_human_author_needs_frozen_on():
    with pytest.raises(ValidationError, match="frozen_on"):
        case(author="human")
    assert case(author="human", frozen_on="2027-01-01").frozen_on == date(2027, 1, 1)


def test_expected_criteria_need_citations():
    with pytest.raises(ValidationError):
        EligibilityCase.model_validate(
            {**case().model_dump(mode="json"), "expected_criteria": [{"rule_id": "credits", "verdict": "meets", "citations": []}]}
        )


def test_unknown_fields_and_bad_values_rejected():
    with pytest.raises(ValidationError):
        case(score=1)
    with pytest.raises(ValidationError):
        case(intake="autumn")
    with pytest.raises(ValidationError):
        case(headline="admitted")


def test_validator_finds_dataset_problems(settings):
    problems = validate_cases(
        [
            case("C01"),
            case("C01"),  # duplicate id
            case("C02", slug="no-such-programme"),
            case("C03", expected_criteria=[{"rule_id": "nope", "verdict": "meets", "citations": [CITE]}]),
            case("C04", related_to="C99"),
        ],
        settings,
    )
    text = "\n".join(problems)
    assert "C01: duplicate case_id" in text
    assert "C02: no rule file" in text
    assert "C03: rule nope" in text
    assert "C04: related_to C99" in text
    assert validate_cases([case("C01"), case("C02", related_to="C01")], settings) == []


def test_load_cases_reads_jsonl_and_reports_the_line(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(case().model_dump_json() + "\n\n" + '{"case_id": "bad"}\n')
    with pytest.raises(ValueError, match="line 3"):
        load_cases(path)
    path.write_text(case().model_dump_json() + "\n")
    assert [c.case_id for c in load_cases(path)] == ["C01"]


# --- runner and metrics ------------------------------------------------------------
def test_agreement_false_positive_and_splits(settings):
    cases = [
        case("C01"),  # engine meets, expected meets
        case("C02", credits="119", headline="does_not_meet_published_requirements", verdict="does_not_meet"),
        # wrong label: expected a failure, engine says meets -> disagreement and a false positive
        case("C03", headline="does_not_meet_published_requirements", verdict="does_not_meet", related_to="C01"),
        case("C04", profile={}, headline="needs_information_or_review", verdict="unknown",
             author="human", frozen_on="2027-01-01"),
    ]
    out = run_cases(cases, settings)
    m = out["metrics"]
    assert m["cases"] == 4
    assert m["headline_agreement"] == {"agree": 3, "total": 4, "rate": 0.75}
    assert m["criterion_agreement"] == {"agree": 3, "total": 4, "rate": 0.75}
    assert m["false_positive_headlines"] == 1
    assert m["by_author"]["human"]["cases"] == 1 and m["by_author"]["human"]["headline_agreement"]["agree"] == 1
    assert m["by_author"]["assisted"]["cases"] == 3
    assert m["per_programme"]["fixture-msc"]["headline_agreement"]["agree"] == 3
    assert m["per_programme"]["fixture-msc"]["false_positive_headlines"] == 1
    assert m["independent_cases"] == 3  # C03 is a variant of C01
    assert m["by_reviewer"]["None"]["cases"] == 4
    assert m["programmes_without_cases"] == []
    assert [d["case_id"] for d in out["disagreements"]] == ["C03"]


def test_coverage_and_unknown_reasons(settings):
    out = run_cases([case("C01"), case("C02", profile={}, headline="needs_information_or_review", verdict="unknown")], settings)
    m = out["metrics"]
    # counted: credits x2 (one decided, one missing fact); the info-only board rule is not counted
    assert m["automatic_check_coverage"] == {"decided": 1, "applicable": 2, "rate": 0.5}
    assert m["unknown_reasons"] == {"missing_fact": 1}


def test_hashes_latency_and_output_file(settings, tmp_path):
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(case().model_dump_json() + "\n")
    out = run_cases(load_cases(cases_path), settings, dataset_path=cases_path)
    h = out["hashes"]
    assert len(h["dataset_sha256"]) == 64
    assert h["programmes"]["fixture-msc"]["record_sha256"] == RULES["record_sha256"]
    assert len(h["programmes"]["fixture-msc"]["ruleset_sha256"]) == 64
    assert len(h["country_groups_sha256"]) == 64
    lat = out["metrics"]["latency_ms"]
    assert 0 <= lat["p50"] <= lat["p95"] <= lat["max"]
    target = tmp_path / "results" / "eligibility_baseline.json"
    write_results(out, target)
    assert json.loads(target.read_text())["metrics"]["cases"] == 1


def test_empty_rates_are_none_not_zero(settings):
    out = run_cases([], settings)
    assert out["metrics"]["headline_agreement"] == {"agree": 0, "total": 0, "rate": None}


# --- command line ------------------------------------------------------------------
def _script():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "scripts" / "eval_eligibility.py"
    spec = importlib.util.spec_from_file_location("eval_eligibility_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_refuses_missing_or_invalid_dataset_and_writes_nothing(settings, tmp_path):
    out = tmp_path / "out.json"
    assert _script().main(["--cases", str(tmp_path / "none.jsonl"), "--out", str(out)], settings) == 1
    bad = tmp_path / "bad.jsonl"
    bad.write_text(case().model_dump_json() + "\n" + case().model_dump_json() + "\n")  # duplicate id
    assert _script().main(["--cases", str(bad), "--out", str(out)], settings) == 1
    unfrozen = tmp_path / "unfrozen.jsonl"
    unfrozen.write_text(json.dumps({**case().model_dump(mode="json"), "author": "human"}) + "\n")
    assert _script().main(["--cases", str(unfrozen), "--out", str(out)], settings) == 1
    assert not out.exists()


def test_script_writes_results(settings, tmp_path):
    cases_path, out = tmp_path / "cases.jsonl", tmp_path / "out.json"
    cases_path.write_text(case().model_dump_json() + "\n")
    assert _script().main(["--cases", str(cases_path), "--out", str(out)], settings) == 0
    assert json.loads(out.read_text())["metrics"]["headline_agreement"]["agree"] == 1


def test_default_dataset_path_is_a_setting():
    s = load_settings()
    assert s.evaluation.eligibility_cases_path.endswith("eligibility_cases.jsonl")
    assert s.evaluation.eligibility_results_out == "evaluation/results/eligibility_baseline.json"


def test_validator_refuses_future_freeze_self_reference_and_broken_rules(settings, tmp_path):
    from pathlib import Path

    problems = validate_cases(
        [case("C01", author="human", frozen_on="2099-01-01"), case("C02", related_to="C02")],
        settings, today=date(2027, 1, 1),
    )
    assert any("C01: frozen_on 2099-01-01 is in the future" in p for p in problems)
    assert any("C02: related_to C02" in p for p in problems)
    (Path(settings.paths.verified_dir) / "fixture-msc.json").unlink()
    assert any("cannot load the rules" in p for p in validate_cases([case()], settings))


def test_schema_refuses_duplicate_expected_rule_and_not_covered():
    with pytest.raises(ValidationError, match="twice"):
        case(expected_criteria=[{"rule_id": "credits", "verdict": "meets", "citations": [CITE]}] * 2)
    with pytest.raises(ValidationError, match="coverage check"):
        case(headline="not_covered")


def test_stale_rules_are_reported_as_stale_not_as_disagreement_noise(settings):
    from pathlib import Path

    path = Path(settings.paths.verified_dir) / "fixture-msc.json"
    path.write_text(json.dumps({"tier": "human", "record": {**RECORD, "extra": 1}}))
    out = run_cases([case("C01", headline="needs_information_or_review")], settings)
    row = out["disagreements"][0]
    assert row["rules_stale"] and row["criteria"][0]["engine"] == "absent"
    assert out["metrics"]["unknown_reasons"] == {"rules_stale": 1}


def test_bom_file_loads(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_bytes(b"\xef\xbb\xbf" + case().model_dump_json().encode() + b"\r\n")
    assert len(load_cases(path)) == 1


def test_p95_is_nearest_rank():
    from evaluation.eligibility_eval import _latency

    assert _latency([float(i) for i in range(1, 32)])["p95"] == 30.0  # ceil(0.95*31) = 30th value
    assert _latency([5.0])["p95"] == 5.0


def test_runner_passes_intake_and_year_to_the_engine(settings):
    from pathlib import Path

    rules = json.loads((Path(settings.paths.rules_dir) / "fixture-msc.json").read_text())
    rules["rules"].append({"id": "deadline", "label": "apply by 15 July", "category": "readiness",
                           "check": {"type": "deadline", "intake": "winter", "close": {"month": 7, "day": 15}},
                           "citations": [CITE], "reviewed_by": "human"})
    (Path(settings.paths.rules_dir) / "fixture-msc.json").write_text(json.dumps(rules))
    expect = [{"rule_id": "deadline", "verdict": "does_not_meet", "citations": [CITE]}]
    late = case(as_of="2027-07-16", expected_criteria=expect)
    assert run_cases([late], settings)["metrics"]["criterion_agreement"]["agree"] == 1
    summer = case(as_of="2027-07-16", intake="summer", expected_criteria=[{**expect[0], "verdict": "not_applicable"}])
    assert run_cases([summer], settings)["metrics"]["criterion_agreement"]["agree"] == 1
