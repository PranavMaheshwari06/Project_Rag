"""Date predicates: application windows by intake and starting year (inclusive
closing day, explicit year offsets, summer deadlines in the previous year) and
maximum test or certificate age (GRE, GATE year-only), all against the
request's `as_of`, never the clock."""

from datetime import date

import pytest

from core.config import load_settings
from eligibility.engine import Target, check_eligibility, evaluate, shift_years
from eligibility.profile import Profile
from eligibility.rules import Rule, RuleSet, load_ruleset

CITE = {"doc_id": "de/x/y", "quote": "q"}
WINTER = {"type": "deadline", "intake": "winter", "close": {"month": 7, "day": 15, "year_offset": 0}}
# summer intake of year Y with a closing day in November of Y-1
SUMMER_PREV = {"type": "deadline", "intake": "summer", "close": {"month": 11, "day": 15, "year_offset": -1}}
WINDOW = {**WINTER, "open": {"month": 6, "day": 1, "year_offset": 0}, "starting_years": [2027]}
GRE_AGE = {"type": "max_age", "fact": "gre.taken_on", "years": 5}
GATE_AGE = {"type": "max_age", "fact": "gate.year", "years": 3}


def ev(check, as_of=date(2027, 7, 15), intake="winter", starting_year=2027, **facts):
    rule = Rule.model_validate({"id": "r", "label": "l", "check": check, "citations": [CITE]})
    return evaluate(rule.check, Profile(**facts), target=Target(as_of=as_of, intake=intake, starting_year=starting_year))


# --- helpers ---------------------------------------------------------------------
@pytest.mark.parametrize("d,n,out", [
    (date(2022, 3, 1), 5, date(2027, 3, 1)),
    (date(2020, 2, 29), 5, date(2025, 2, 28)),  # no 29 February: the last day of February
    (date(2024, 2, 29), 4, date(2028, 2, 29)),
    (date(2027, 1, 15), -1, date(2026, 1, 15)),
])
def test_shift_years(d, n, out):
    assert shift_years(d, n) == out


# --- deadlines --------------------------------------------------------------------
def test_closing_day_is_inclusive():
    on = ev(WINTER, as_of=date(2027, 7, 15))
    assert on.verdict == "meets" and on.margin == 0
    after = ev(WINTER, as_of=date(2027, 7, 16))
    assert after.verdict == "does_not_meet" and after.margin == -1
    assert ev(WINTER, as_of=date(2027, 7, 1)).margin == 14


def test_year_offset_puts_a_summer_deadline_in_the_previous_year():
    assert ev(SUMMER_PREV, intake="summer", starting_year=2027, as_of=date(2026, 11, 15)).verdict == "meets"
    assert ev(SUMMER_PREV, intake="summer", starting_year=2027, as_of=date(2026, 11, 16)).verdict == "does_not_meet"
    # year boundary: 31 December and 1 January of the starting year are both late
    assert ev(SUMMER_PREV, intake="summer", starting_year=2027, as_of=date(2026, 12, 31)).verdict == "does_not_meet"
    assert ev(SUMMER_PREV, intake="summer", starting_year=2027, as_of=date(2027, 1, 1)).margin == -47


def test_other_intake_is_not_applicable_and_missing_context_is_unknown():
    assert ev(WINTER, intake="summer").verdict == "not_applicable"
    for kw in ({"intake": None}, {"starting_year": None}, {"as_of": None}):
        r = ev(WINTER, **kw)
        assert r.verdict == "unknown" and r.reason == "missing_request_date"


def test_window_before_opening_is_still_open_and_dates_are_shown():
    r = ev(WINDOW, as_of=date(2027, 5, 31))
    assert r.verdict == "meets" and "opens 2027-06-01" in r.entered and r.required == "apply by 2027-07-15"


def test_dates_published_only_for_some_years_stay_unknown_for_others():
    r = ev(WINDOW, starting_year=2028, as_of=date(2028, 7, 1))
    assert r.verdict == "unknown" and r.reason == "deadline_not_published_for_year"


def test_deadline_rejects_impossible_dates():
    with pytest.raises(ValueError):
        Rule.model_validate({"id": "r", "label": "l", "citations": [CITE],
                             "check": {**WINTER, "close": {"month": 2, "day": 30, "year_offset": 0}}})


# --- test and certificate age ---------------------------------------------------------
def test_gre_age_last_day_and_day_after():
    taken = date(2022, 7, 15)
    assert ev(GRE_AGE, as_of=date(2027, 7, 15), gre={"taken_on": taken}).verdict == "meets"
    late = ev(GRE_AGE, as_of=date(2027, 7, 16), gre={"taken_on": taken})
    assert late.verdict == "does_not_meet" and late.margin == -1


def test_age_unknowns_and_no_test():
    assert ev(GRE_AGE, gre={"quant": "165"}).reason == "missing_fact"
    assert ev(GRE_AGE, as_of=None, gre={"taken_on": date(2026, 1, 1)}).reason == "missing_request_date"
    assert ev(GRE_AGE, gre="none").verdict == "does_not_meet"


def test_gate_year_only_decides_only_when_the_whole_year_agrees():
    # 3 years from any day of 2024 reaches into 2027: 1 May 2027 lies inside for an
    # early-2024 result and outside for a late-2024 one, so the year alone cannot decide
    r = ev(GATE_AGE, as_of=date(2027, 5, 1), gate={"year": 2024})
    assert r.verdict == "unknown" and r.reason == "date_imprecise"
    # fresh for certain only while even 1 January of that year is within 3 years
    assert ev(GATE_AGE, as_of=date(2027, 1, 1), gate={"year": 2024}).verdict == "meets"
    assert ev(GATE_AGE, as_of=date(2027, 1, 2), gate={"year": 2024}).reason == "date_imprecise"
    # stale for certain once even 31 December of that year is older than 3 years
    assert ev(GATE_AGE, as_of=date(2027, 12, 31), gate={"year": 2024}).reason == "date_imprecise"
    assert ev(GATE_AGE, as_of=date(2028, 1, 1), gate={"year": 2024}).verdict == "does_not_meet"
    assert ev(GATE_AGE, as_of=date(2027, 5, 1), gate={"year": 2025}).verdict == "meets"


# --- report -------------------------------------------------------------------------
def test_missed_deadline_is_readiness_not_academic():
    rs = RuleSet(slug="s", record_sha256="x", rules=[
        {"id": "credits", "label": "credits", "check": {"type": "min", "fact": "total_credits", "value": "1"},
         "citations": [CITE], "reviewed_by": "human"},
        {"id": "deadline", "label": "Apply by 15 July for the winter term", "category": "readiness",
         "check": WINTER, "citations": [CITE], "reviewed_by": "human"},
    ])
    rep = check_eligibility(Profile(total_credits="1"), rs, as_of=date(2027, 7, 16), intake="winter", starting_year=2027)
    assert rep.headline == "meets_checked_published_requirements"
    assert rep.readiness.headline == "items_still_needed"
    assert rep.criteria[1].action.startswith("Application window closed")
    assert (rep.intake, rep.starting_year) == ("winter", 2027)


@pytest.mark.parametrize("slug,as_of,verdict", [  # non-EU applicant
    ("kit-m-sc-computer-science", date(2027, 6, 15), "meets"),
    ("kit-m-sc-computer-science", date(2027, 6, 16), "does_not_meet"),
    ("kit-m-sc-computational-and-data-science", date(2027, 7, 15), "meets"),
    ("kit-m-sc-computational-and-data-science", date(2027, 7, 16), "does_not_meet"),
])
def test_kit_winter_deadlines(slug, as_of, verdict):
    settings = load_settings()
    rules, stale = load_ruleset(settings, slug)
    rep = check_eligibility(Profile(citizenships=["India"]), rules, stale, as_of=as_of, intake="winter", starting_year=2027)
    crit = next(c for c in rep.criteria if c.rule_id == "deadline_winter")
    assert crit.verdict == verdict and crit.category == "readiness"
    assert next(c for c in rep.criteria if c.rule_id == "deadline_summer").verdict == "not_applicable"
    assert next(r for r in rules.rules if r.id == "deadline_winter").reviewed_by == "pending"


def test_kit_cds_deadline_depends_on_citizenship():
    settings = load_settings()
    rules, stale = load_ruleset(settings, "kit-m-sc-computational-and-data-science")

    def winter(citizenships, as_of):
        rep = check_eligibility(Profile(citizenships=citizenships), rules, stale,
                                as_of=as_of, intake="winter", starting_year=2027)
        return next(c for c in rep.criteria if c.rule_id == "deadline_winter").verdict

    assert winter(["Germany"], date(2027, 7, 16)) == "meets"  # German and EU nationals: 30 September
    assert winter(["Germany"], date(2027, 9, 30)) == "meets"
    assert winter(["Germany"], date(2027, 10, 1)) == "does_not_meet"
    assert winter(["India", "Italy"], date(2027, 9, 1)) == "meets"  # one EU citizenship is enough
    assert winter(["India"], date(2027, 9, 1)) == "does_not_meet"
    unknown = check_eligibility(Profile(), rules, stale, as_of=date(2027, 7, 16), intake="winter", starting_year=2027)
    assert next(c for c in unknown.criteria if c.rule_id == "deadline_winter").verdict == "unknown"


def test_cli_takes_the_request_date_intake_and_year(capsys, monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("check_eligibility_cli", root / "scripts" / "check_eligibility.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    # the shared cached settings may have been repointed by the corpus fixture of the full suite
    monkeypatch.setattr(cli, "get_settings", load_settings)
    monkeypatch.setattr(sys, "argv", [
        "x", "--profile", str(root / "data/eligibility/examples/synthetic_kit_cs.json"),
        "--programme", "kit-m-sc-computer-science", "--as-of", "2027-06-16",
        "--intake", "winter", "--starting-year", "2027"])
    assert cli.main() == 0
    out = capsys.readouterr().out
    assert "readiness: items_still_needed (1 does_not_meet)" in out
    assert "Application window closed: Apply by 15 June for the winter term." in out


def kit(slug, citizenships, as_of, rule_id="deadline_winter", intake="winter"):
    rules, stale = load_ruleset(load_settings(), slug)
    rep = check_eligibility(Profile(citizenships=citizenships), rules, stale,
                            as_of=as_of, intake=intake, starting_year=2027)
    return next(c for c in rep.criteria if c.rule_id == rule_id)


def test_kit_cds_late_shows_window_closed_with_date_and_days():
    c = kit("kit-m-sc-computational-and-data-science", ["India"], date(2027, 7, 16))
    assert c.action.startswith("Application window closed")
    assert c.required == "apply by 2027-07-15" and c.margin == -1


def test_unknown_citizenship_keeps_the_other_intake_not_applicable():
    cds = "kit-m-sc-computational-and-data-science"
    assert kit(cds, None, date(2027, 7, 16), rule_id="deadline_summer").verdict == "not_applicable"
    assert kit(cds, None, date(2027, 7, 16)).verdict == "unknown"


def test_open_after_close_is_rejected():
    with pytest.raises(ValueError, match="open after it closes"):
        Rule.model_validate({"id": "r", "label": "l", "citations": [CITE],
                             "check": {**WINTER, "open": {"month": 8, "day": 1}}})


def test_max_age_refuses_a_bool_and_a_result_after_as_of():
    with pytest.raises(ValueError, match="not a date or a year"):
        ev({"type": "max_age", "fact": "degree_completed", "years": 3}, degree_completed=True)
    assert ev(GATE_AGE, as_of=date(2027, 5, 1), gate={"year": 2031}).reason == "date_after_as_of"
    assert ev(GRE_AGE, as_of=date(2027, 5, 1), gre={"taken_on": date(2027, 5, 2)}).reason == "date_after_as_of"


@pytest.mark.parametrize("as_of,verdict", [(date(2029, 2, 28), "meets"), (date(2029, 3, 1), "does_not_meet")])
def test_leap_day_result(as_of, verdict):
    assert ev(GRE_AGE, as_of=as_of, gre={"taken_on": date(2024, 2, 29)}).verdict == verdict


def test_kit_cs_pending_rules_are_exactly_the_unreviewed_ones():
    rules, _ = load_ruleset(load_settings(), "kit-m-sc-computer-science")
    assert {r.id for r in rules.rules if r.reviewed_by == "pending"} == {
        "degree", "degree_ects", "module_assignment", "test_validity", "english", "deadline_winter", "deadline_summer"}
