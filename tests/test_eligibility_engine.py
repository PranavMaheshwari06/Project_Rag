"""Worked boundary examples, small enough to check by hand.

Checked and accepted by the maintainer on 2026-10-29 (items C1-C10 in LEARNING.md):
grade conversion, bounds and margins, missing vs zero, group logic, headline rules."""

from decimal import Decimal as D

import pytest

from eligibility.engine import check_eligibility, check_funds, evaluate
from eligibility.grade import convert_grade
from eligibility.profile import Profile
from eligibility.rules import Rule, RuleSet

CITE = {"doc_id": "de/x/y", "quote": "q"}


def mn(fact, value, strict=False):
    return {"type": "min", "fact": fact, "value": value, "strict": strict}


def mx(fact, value, strict=False):
    return {"type": "max", "fact": fact, "value": value, "strict": strict}


def group(kind, *children):
    return {"type": kind, "children": list(children)}


def ev(check, **facts):
    return evaluate(
        Rule.model_validate(
            {"id": "r", "label": "l", "check": check, "citations": [CITE]}
        ).check,
        Profile(**facts),
    )


# --- grade conversion ---------------------------------------------------------
@pytest.mark.parametrize(
    "best,passing,obtained,german",
    [
        ("4.0", "2.0", "3.0", "2.5"),  # 1 + 3*(4-3)/(4-2)
        ("100", "50", "75", "2.5"),  # 1 + 3*25/50
        ("1.0", "4.0", "2.0", "2.0"),  # German scale: 1 + 3*(1-2)/(1-4)
        ("10", "5", "10", "1"),  # best grade -> 1.0
        ("10", "5", "5", "4"),  # passing grade -> 4.0
    ],
)
def test_convert_grade(best, passing, obtained, german):
    r = convert_grade(D(best), D(passing), D(obtained))
    assert r.german == D(german) and r.estimate


def test_convert_grade_keeps_precision():
    assert convert_grade(D(10), D(5), D(8)).german == D("2.2")  # 1 + 3*2/5
    assert convert_grade(D(3), D(1), D(2)).german == D("2.5")


def test_convert_grade_rejects_bad_scales():
    with pytest.raises(ValueError):
        convert_grade(D(4), D(4), D(4))
    with pytest.raises(ValueError):
        convert_grade(D(4), D(2), D(1))  # below passing
    with pytest.raises(ValueError):
        convert_grade(D(4), D(2), D(5))  # above best


# --- bounds and margins -------------------------------------------------------
def test_minimum_boundary():
    assert ev(mn("total_credits", "120"), total_credits="120").verdict == "meets"
    assert ev(mn("total_credits", "120"), total_credits="120").margin == 0
    r = ev(mn("total_credits", "120"), total_credits="119.5")
    assert (r.verdict, r.margin) == ("does_not_meet", D("-0.5"))


def test_strict_bound_fails_at_zero_margin():
    r = ev(mn("total_credits", "120", strict=True), total_credits="120")
    assert (r.verdict, r.margin) == ("does_not_meet", 0)
    assert (
        ev(mn("total_credits", "120", strict=True), total_credits="120.1").verdict
        == "meets"
    )


def test_maximum_margin_is_favourable_when_below():
    r = ev(mx("funds_eur", "100"), funds_eur="90")
    assert (r.verdict, r.margin) == ("meets", D("10"))
    assert ev(mx("funds_eur", "100"), funds_eur="101").verdict == "does_not_meet"


def test_missing_is_unknown_but_zero_is_a_fail():
    assert ev(mn("total_credits", "120")).verdict == "unknown"
    assert ev(mn("total_credits", "120"), total_credits="0").verdict == "does_not_meet"
    assert (
        ev(
            mn("subject_credits.mathematics", "20"), subject_credits={"physics": "30"}
        ).reason
        == "missing_fact"
    )
    assert (
        ev(
            mn("subject_credits.mathematics", "20"),
            subject_credits={"mathematics": "0"},
        ).verdict
        == "does_not_meet"
    )


def test_unknown_fact_path_and_non_numeric_raise():
    with pytest.raises(ValueError):
        ev(mn("nonsense", "1"), total_credits="1")
    with pytest.raises(ValueError):
        ev(mn("degree_title", "1"), degree_title="BSc")


def test_funds_surplus_and_shortfall():
    assert check_funds(D("12000"), D("11904")).margin == D("96")
    r = check_funds(D("11000"), D("11904"))
    assert (r.verdict, r.margin) == ("does_not_meet", D("-904"))
    assert check_funds(None, D("11904")).verdict == "unknown"


# --- groups -------------------------------------------------------------------
PASS, FAIL, UNK = (
    mn("total_credits", "100"),
    mn("total_credits", "999"),
    mn("funds_eur", "1"),
)


@pytest.mark.parametrize(
    "kind,children,expected",
    [
        ("any_of", [FAIL, PASS], "meets"),
        ("any_of", [FAIL, UNK], "unknown"),  # an unresolved alternative keeps it open
        ("any_of", [FAIL, FAIL], "does_not_meet"),
        ("all_of", [PASS, PASS], "meets"),
        ("all_of", [PASS, UNK], "unknown"),
        ("all_of", [FAIL, UNK], "does_not_meet"),  # a known failure is enough
    ],
)
def test_group_logic(kind, children, expected):
    assert ev(group(kind, *children), total_credits="120").verdict == expected


def test_university_review_never_meets():
    r = ev({"type": "university_review", "note": "board decides"})
    assert (r.verdict, r.reason) == ("unknown", "university_review")
    assert (
        ev(
            group("any_of", PASS, {"type": "university_review", "note": "n"}),
            total_credits="120",
        ).verdict
        == "meets"
    )


# --- headline -----------------------------------------------------------------
def ruleset(*rules, reviewed="human"):
    return RuleSet(
        slug="s",
        record_sha256="x",
        rules=[
            {
                "id": f"r{i}",
                "label": f"rule {i}",
                "check": c,
                "citations": [CITE],
                "reviewed_by": reviewed,
                **extra,
            }
            for i, (c, extra) in enumerate(rules)
        ],
    )


def test_headline_pass_fail_unknown():
    p = Profile(total_credits="120")
    assert (
        check_eligibility(p, ruleset((PASS, {}))).headline
        == "meets_checked_published_requirements"
    )
    assert (
        check_eligibility(p, ruleset((PASS, {}), (FAIL, {}))).headline
        == "does_not_meet_published_requirements"
    )
    assert (
        check_eligibility(p, ruleset((PASS, {}), (UNK, {}))).headline
        == "needs_information_or_review"
    )


def test_soft_and_finance_rules_do_not_move_the_headline():
    p = Profile(total_credits="120")
    rs = ruleset(
        (PASS, {}), (FAIL, {"severity": "soft"}), (FAIL, {"category": "finance"})
    )
    rep = check_eligibility(p, rs)
    assert rep.headline == "meets_checked_published_requirements"
    assert [c.verdict for c in rep.criteria] == [
        "meets",
        "does_not_meet",
        "does_not_meet",
    ]


def test_pending_review_or_no_rules_never_gives_a_positive_headline():
    p = Profile(total_credits="120")
    assert (
        check_eligibility(p, ruleset((PASS, {}), reviewed="pending")).headline
        == "needs_information_or_review"
    )
    assert check_eligibility(p, ruleset()).headline == "needs_information_or_review"


def test_stale_rules_produce_no_verdicts():
    rep = check_eligibility(
        Profile(total_credits="120"), ruleset((FAIL, {})), stale=True
    )
    assert (
        rep.headline == "needs_information_or_review"
        and rep.rules_stale
        and rep.criteria == []
    )


def test_one_criterion_per_top_level_rule():
    rep = check_eligibility(
        Profile(total_credits="120"), ruleset((group("any_of", FAIL, PASS), {}))
    )
    assert len(rep.criteria) == 1


# --- numeric matches, grade share, German level --------------------------------
def test_in_matches_numbers_by_value():
    four_point = {"type": "in", "fact": "grade.best", "values": ["4", "100"]}
    g = {"obtained": "3.2", "passing": "2"}
    assert ev(four_point, grade={**g, "best": "4.0"}).verdict == "meets"
    assert ev(four_point, grade={**g, "best": "10"}).verdict == "does_not_meet"
    assert ev({"type": "in", "fact": "gate.year", "values": ["2026"]}, gate={"year": 2026}).verdict == "meets"
    # strings that are not numbers keep the case-insensitive match
    assert ev({"type": "in", "fact": "gate.paper", "values": ["CS"]}, gate={"paper": "cs"}).verdict == "meets"


def test_percent_of_best():
    g = {"obtained": "3.0", "best": "4", "passing": "2"}
    assert ev(mn("grade.percent_of_best", "75"), grade=g).margin == D("0")
    assert ev(mn("grade.percent_of_best", "75"), grade={**g, "obtained": "2.99"}).verdict == "does_not_meet"
    assert ev(mn("grade.percent_of_best", "75")).verdict == "unknown"  # no grade given


def test_german_level_is_cefr():
    c1 = {"type": "in", "fact": "german_level", "values": ["C1", "C2"]}
    assert ev(c1, german_level="C2").verdict == "meets"
    assert ev(c1, german_level="B2").verdict == "does_not_meet"
    assert ev(c1).verdict == "unknown"
    with pytest.raises(ValueError):
        Profile(german_level="fluent")
