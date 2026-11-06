"""Real rule files for TU Berlin, TU Dresden and Stuttgart Computer Science."""

import pytest

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import load_ruleset

TUB = "tu-berlin-m-sc-computer-science"
TUD = "tu-dresden-m-sc-computer-science"
STU = "university-of-stuttgart-m-sc-computer-science"


def report(slug, **facts):
    return check_eligibility(Profile(**facts), *load_ruleset(load_settings(), slug))


def crit(slug, rule_id, **facts):
    return {c.rule_id: c for c in report(slug, **facts).criteria}[rule_id]


def lang(*entries):
    return {"language": list(entries)}


@pytest.mark.parametrize("slug", [TUB, TUD, STU])
def test_rule_files_are_current_and_reviewed(slug):
    rules, stale = load_ruleset(load_settings(), slug)
    assert not stale
    # rules changed or added after the 2026-11-02 review await it again
    awaiting = {"degree", "subject_allocation", "english_components"} if slug == TUB else set()
    assert {r.id for r in rules.rules if r.reviewed_by != "human"} == awaiting


@pytest.mark.parametrize("slug", [TUB, TUD, STU])
def test_degree_equivalence_is_the_universitys_call(slug):
    c = crit(slug, "degree", degree_title="B.Sc. Computer Science", degree_completed=True)
    assert (c.verdict, c.reason, c.severity) == ("unknown", "university_review", "hard")


# --- TU Berlin ------------------------------------------------------------------
FULL = {"foundations_total": "36", "theoretical_cs": "12", "computer_engineering": "12",
        "practical_cs": "12", "mathematics": "18", "additional_cs": "30"}
AREAS = list(FULL)


@pytest.mark.parametrize("area", AREAS)
def test_tub_credit_boundaries(area):
    ok = lambda **sc: crit(TUB, area, subject_credits=sc).verdict  # noqa: E731
    assert ok(**{area: FULL[area]}) == "meets"                                 # exactly the minimum
    assert ok(**{area: str(int(FULL[area]) - 1)}) == "does_not_meet"           # one short
    assert ok(**{area: "0"}) == "does_not_meet"                                # said zero: a gap, not unknown
    assert crit(TUB, area).verdict == "unknown"                                # nothing entered


def test_tub_foundations_total_is_not_counted_twice():
    # the total and its three areas are separate facts: a 36 total does not satisfy theory
    r = {c.rule_id: c.verdict for c in report(TUB, subject_credits={**FULL, "theoretical_cs": "11"}).criteria}
    assert r["foundations_total"] == "meets"
    assert r["theoretical_cs"] == "does_not_meet"
    assert r["computer_engineering"] == r["practical_cs"] == "meets"
    # areas fine but total entered short: total fails on its own
    r = {c.rule_id: c.verdict for c in report(TUB, subject_credits={**FULL, "foundations_total": "35"}).criteria}
    assert r["foundations_total"] == "does_not_meet" and r["theoretical_cs"] == "meets"


def test_tub_english_routes():
    eng = lambda **f: crit(TUB, "english", **f)  # noqa: E731
    assert eng(**lang({"test": "IELTS", "overall": "6.5"})).verdict == "meets"
    # 5.5 shows B2 but is not enough; other Faculty IV proof may exist, so unknown, never a fail
    assert eng(**lang({"test": "IELTS", "overall": "5.5"}), degree_country="India").verdict == "unknown"
    assert eng(**lang({"test": "IELTS", "overall": "6.0"})).verdict == "unknown"
    assert eng(degree_completed=True, degree_country="United States of America").verdict == "meets"
    assert eng(degree_completed=True, degree_country="Singapore").verdict == "meets"
    # an English-taught degree elsewhere is not accepted; neither is an unfinished native degree
    assert eng(degree_completed=True, degree_country="Germany", english_instruction_share="100").verdict == "unknown"
    assert eng(degree_completed=False, degree_country="Canada").verdict == "unknown"
    assert eng().verdict == "unknown"


def test_tub_vpd_depends_on_the_degree_country():
    vpd = lambda **f: crit(TUB, "vpd", **f)  # noqa: E731
    assert vpd(degree_country="Germany").verdict == "not_applicable"
    assert vpd(degree_country="India", documents=[]).verdict == "does_not_meet"
    assert vpd(degree_country="India", documents=["vpd"]).verdict == "meets"
    assert vpd(degree_country="India").verdict == "unknown"
    assert vpd(documents=["vpd"]).verdict == "unknown"      # no country: never silently exempt


def test_tub_headline_not_positive_while_the_university_decides():
    p = dict(subject_credits=FULL, **lang({"test": "IELTS", "overall": "7"}), degree_country="Germany")
    rep = report(TUB, **p)
    assert rep.headline == "needs_information_or_review"
    assert {c.rule_id for c in rep.criteria if c.reason == "university_review"} == {"degree", "subject_allocation"}
    # a failing credit area is a known failure; missing readiness documents never are
    short = report(TUB, **{**p, "subject_credits": {**FULL, "mathematics": "17"}})
    assert short.headline == "does_not_meet_published_requirements"
    foreign = report(TUB, **{**p, "degree_country": "India", "documents": []})
    assert foreign.headline == "needs_information_or_review"


# --- TU Dresden -----------------------------------------------------------------
def test_tud_english_boundaries():
    eng = lambda *e: crit(TUD, "english", **lang(*e)).verdict  # noqa: E731
    assert eng({"test": "IELTS", "overall": "7.0"}) == "meets"
    assert eng({"test": "TOEFL iBT", "overall": "95"}) == "meets"
    assert eng({"test": "TOEFL iBT (2026 scale)", "overall": "5.0"}) == "meets"
    # just below every route: another C1 test may still be accepted, so unknown and not a fail
    r = crit(TUD, "english", **lang({"test": "IELTS", "overall": "6.5"}, {"test": "TOEFL iBT", "overall": "94"}))
    assert (r.verdict, r.reason) == ("unknown", "university_review")
    assert eng({"test": "TOEFL iBT (2026 scale)", "overall": "4.5"}) == "unknown"
    assert eng() == "unknown"
    assert crit(TUD, "english").verdict == "unknown"


def test_tud_aps_for_china_vietnam_india():
    aps = lambda **f: crit(TUD, "aps", **f)  # noqa: E731
    for country in ("China", "Vietnam", "India"):
        assert aps(degree_country=country, documents=[]).verdict == "does_not_meet"
        assert aps(degree_country=country, documents=["aps_certificate"]).verdict == "meets"
    assert aps(degree_country="Germany").verdict == "not_applicable"
    assert aps(degree_country="Nepal").verdict == "not_applicable"   # only the published countries
    assert aps(documents=["aps_certificate"]).verdict == "unknown"    # unknown country: never exempt
    assert aps(degree_country="India").verdict == "unknown"


def test_tud_headline_not_positive_while_aptitude_is_open():
    apt = crit(TUD, "aptitude_assessment", interview_passed=True)
    assert (apt.verdict, apt.reason, apt.severity) == ("unknown", "university_review", "hard")
    rep = report(TUD, **lang({"test": "IELTS", "overall": "8"}), degree_country="Germany")
    assert rep.headline == "needs_information_or_review"
    # a known English failure cannot happen (review child), so a missing APS never fails the headline
    rep = report(TUD, degree_country="India", documents=[])
    assert rep.headline == "needs_information_or_review"


# --- University of Stuttgart ------------------------------------------------------
def test_stuttgart_english_numeric_boundaries():
    def eng(test, score):
        return crit(STU, "english", **lang({"test": test, "overall": score}), citizenships=["India"]).verdict
    assert eng("IELTS", "7.0") == "meets" and eng("IELTS", "6.5") == "does_not_meet"
    assert eng("TOEFL iBT", "95") == "meets" and eng("TOEFL iBT", "94") == "does_not_meet"
    assert eng("TOEFL iBT (2026 scale)", "5") == "meets" and eng("TOEFL iBT (2026 scale)", "4.5") == "does_not_meet"
    assert eng("PTE Academic", "76") == "meets" and eng("PTE Academic", "75") == "does_not_meet"


def test_stuttgart_english_named_certificates():
    eng = lambda e: crit(STU, "english", **lang(e), citizenships=["India"]).verdict  # noqa: E731
    assert eng({"test": "CAE", "grade": "C"}) == "meets"
    assert eng({"test": "CPE", "grade": "A"}) == "meets"
    assert eng({"test": "CAE", "grade": "Level B2"}) == "does_not_meet"   # issued at a lower level
    assert eng({"test": "Oxford Test of English Advanced", "grade": "C1"}) == "meets"
    assert eng({"test": "Oxford Test of English Advanced", "grade": "B2"}) == "does_not_meet"
    assert eng({"test": "telc", "grade": "C1"}) == "meets"
    assert eng({"test": "telc University", "grade": "very good"}) == "meets"
    assert eng({"test": "telc University", "grade": "good"}) == "does_not_meet"


def test_stuttgart_unknown_versus_fail():
    eng = lambda **f: crit(STU, "english", **f)  # noqa: E731
    low = lang({"test": "IELTS", "overall": "6.5"})
    # citizenship not given: the native-English exception is still open
    assert eng(**low).verdict == "unknown"
    assert eng().verdict == "unknown"
    # citizenship given and not listed: every route is closed (the list of proofs is closed)
    assert eng(**low, citizenships=["India"]).verdict == "does_not_meet"
    assert eng(**lang(), citizenships=["India"]).verdict == "does_not_meet"
    # medium of instruction is not accepted
    assert eng(english_instruction_share="100", citizenships=["India"], **lang()).verdict == "does_not_meet"


def test_stuttgart_native_english_exception_is_never_automatic():
    for country in ("Canada", "United Kingdom", "USA", "Malta"):
        r = crit(STU, "english", **lang(), citizenships=[country])
        assert (r.verdict, r.reason) == ("unknown", "university_review")   # education level undecided
    # dual citizens: any listed citizenship opens the route
    assert crit(STU, "english", **lang(), citizenships=["India", "Ireland"]).verdict == "unknown"
    assert crit(STU, "english", **lang(), citizenships=["Singapore"]).verdict == "does_not_meet"  # not on this list


def test_stuttgart_validity_and_board_stay_with_the_university():
    for rule_id in ("english_validity", "admission_board"):
        c = crit(STU, rule_id, **lang({"test": "IELTS", "overall": "8", "taken_on": "2025-01-01"}))
        assert (c.verdict, c.reason, c.severity) == ("unknown", "university_review", "hard")


def test_stuttgart_headline_not_positive_while_a_hard_review_remains():
    rep = report(STU, **lang({"test": "IELTS", "overall": "8"}), citizenships=["India"])
    assert crit(STU, "english", **lang({"test": "IELTS", "overall": "8"})).verdict == "meets"
    assert rep.headline == "needs_information_or_review"
    failing = report(STU, **lang({"test": "IELTS", "overall": "6"}), citizenships=["India"])
    assert failing.headline == "does_not_meet_published_requirements"
