"""Saarland University M.Sc. Computer Science and Data Science and AI rule files."""

import json
from pathlib import Path

import pytest

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import load_ruleset, uncited_quotes

SLUGS = ["saarland-university-m-sc-computer-science", "saarland-university-m-sc-data-science-and-artificial-intelligence"]
both = pytest.mark.parametrize("slug", SLUGS)


def rep(slug, **facts):
    return {c.rule_id: c for c in check_eligibility(Profile(**facts), *load_ruleset(load_settings(), slug)).criteria}


def grade(obtained, best, rank=None):
    return {"obtained": obtained, "best": best, "passing": "0", "class_rank_percentile": rank}


@both
def test_rule_files_are_fresh_reviewed_and_cited(slug):
    s = load_settings()
    rules, stale = load_ruleset(s, slug)
    record = json.loads((Path(s.paths.verified_dir) / f"{slug}.json").read_text())["record"]
    assert not stale
    assert {r.id for r in rules.rules if r.reviewed_by != "human"} == set()
    # only the subject-area sentence (and the English exceptions for DSAI) cite the page beyond the record
    assert {r for r, _, _ in uncited_quotes(rules, record)} <= {"curricular_content", "english"}


@both
def test_grade_percentage_boundary(slug):
    g = lambda o: rep(slug, grade=grade(o, "100"))["grade_cgpa"]  # noqa: E731
    assert g("75").verdict == "meets"
    assert g("74.9").verdict == "does_not_meet"
    assert rep(slug, grade=grade("99", "100"))["grade_cgpa"].verdict == "meets"


@both
def test_grade_four_point_boundary(slug):
    g = lambda o: rep(slug, grade=grade(o, "4.0"))["grade_cgpa"]  # noqa: E731
    assert g("3.00").verdict == "meets"
    assert g("2.99").verdict == "does_not_meet"


@both
def test_grade_other_scale_is_left_to_the_university_never_a_fail(slug):
    r = rep(slug, grade=grade("7.5", "10"))["grade_cgpa"]  # Indian 10-point CGPA
    assert (r.verdict, r.reason) == ("unknown", "university_review")
    assert rep(slug, grade=grade("1.0", "10"))["grade_cgpa"].verdict == "unknown"  # even a low one
    assert rep(slug)["grade_cgpa"].verdict == "unknown"  # no grade given


@both
def test_class_rank_is_top_ten_percent(slug):
    rank = lambda p: rep(slug, grade=grade("80", "100", p))["class_rank"]  # noqa: E731
    assert rank("10").verdict == "meets"
    assert rank("10.1").verdict == "does_not_meet"
    assert rep(slug, grade=grade("80", "100"))["class_rank"].verdict == "unknown"  # rank not supplied
    # a good grade does not make up for a missing rank: the two rules are separate
    assert rep(slug, grade=grade("95", "100", "30"))["grade_cgpa"].verdict == "meets"


@both
def test_gre_or_gate_by_degree_country(slug):
    t = lambda country, **f: rep(slug, degree_country=country, **f)["entrance_test"]  # noqa: E731
    gre = {"quant": "150"}                                  # no minimum score: any result counts
    assert t("India", gre=gre).verdict == "meets"
    assert t("India", gate={"paper": "CS", "qualified": False}).verdict == "meets"  # no cutoff on GATE either
    assert t("India").verdict == "unknown"                  # no result supplied: asks for it
    for exempt in ("Germany", "Switzerland", "United Kingdom", "UK"):
        assert t(exempt).verdict == "not_applicable"
    assert t("Canada").verdict == "unknown"                 # not EHEA: test needed
    assert t("China", gre=gre).verdict == "meets"


@both
def test_exemption_is_never_granted_on_unknown(slug):
    assert rep(slug)["entrance_test"].verdict == "unknown"                       # degree country missing
    assert rep(slug, gre={"quant": "150"})["entrance_test"].verdict == "unknown"  # a result does not decide the condition
    # Russia is listed in the EHEA but suspended: the university decides, never silently exempt
    r = rep(slug, degree_country="Russia")["entrance_test"]
    assert (r.verdict, r.reason) == ("unknown", "group_membership_uncertain")
    assert rep(slug, citizenships=["Germany"], school_country="Germany")["entrance_test"].verdict == "unknown"


@both
def test_english_routes_and_boundaries(slug):
    eng = lambda *entries, **f: rep(slug, language=list(entries), degree_country="India",  # noqa: E731
                                   school_country="India", citizenships=["India"], **f)["english"]
    assert eng({"test": "IELTS", "overall": "7.0"}).verdict == "meets"
    assert eng({"test": "IELTS", "overall": "6.5"}).verdict == "does_not_meet"
    assert eng({"test": "TOEFL iBT", "overall": "95"}).verdict == "meets"
    assert eng({"test": "TOEFL iBT", "overall": "94"}).verdict == "does_not_meet"
    assert eng({"test": "TOEFL PBT", "overall": "600"}).verdict == "meets"
    assert eng({"test": "TOEFL PBT", "overall": "599"}).verdict == "does_not_meet"
    assert eng({"test": "PTE Academic", "overall": "76"}).verdict == "meets"
    assert eng({"test": "PTE Academic", "overall": "75"}).verdict == "does_not_meet"
    assert eng({"test": "CAE", "grade": "C"}).verdict == "meets"
    assert eng({"test": "CPE", "grade": "A"}).verdict == "meets"
    assert eng({"test": "CAE", "grade": "B2"}).verdict == "does_not_meet"  # a lower-level certificate
    # a university letter or an English-taught degree is not accepted
    assert eng(english_instruction_share="100").verdict == "does_not_meet"
    assert eng().verdict == "does_not_meet"  # said no test at all
    # any one test is enough
    assert eng({"test": "IELTS", "overall": "6.0"}, {"test": "TOEFL iBT", "overall": "100"}).verdict == "meets"


@both
def test_english_unknown_is_not_a_fail(slug):
    assert rep(slug)["english"].verdict == "unknown"
    # tests given but where the student studied and holds citizenship is missing: an exception might apply
    r = rep(slug, language=[{"test": "IELTS", "overall": "6.5"}])["english"]
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")
    assert rep(slug, language=[{"test": "CAE"}])["english"].verdict == "unknown"  # grade not supplied


@both
def test_english_native_speaker_and_study_exceptions_go_to_the_university(slug):
    weak = [{"test": "IELTS", "overall": "6.0"}]
    base = {"language": weak, "degree_country": "India", "school_country": "India"}
    assert rep(slug, **base, citizenships=["India"])["english"].verdict == "does_not_meet"
    for field, other in (("degree_country", {"school_country": "India", "citizenships": ["India"]}),
                         ("school_country", {"degree_country": "India", "citizenships": ["India"]}),
                         ("citizenships", {"degree_country": "India", "school_country": "India"})):
        for country in ("Canada", "United States"):
            value = [country] if field == "citizenships" else country
            r = rep(slug, language=weak, **other, **{field: value})["english"]
            assert (r.verdict, r.reason) == ("unknown", "university_review"), (field, country)
    # German school certificates are examined individually
    assert rep(slug, **base, citizenships=["Germany"])["english"].verdict == "unknown"
    # a passing test still decides, whatever the exceptions
    assert rep(slug, language=[{"test": "IELTS", "overall": "7"}], citizenships=["Canada"])["english"].verdict == "meets"


@both
def test_english_new_toefl_scale_is_a_separate_test(slug):
    base = {"degree_country": "India", "school_country": "India", "citizenships": ["India"]}
    new = lambda score: rep(slug, language=[{"test": "TOEFL iBT (2026 scale)", "overall": score}], **base)["english"]  # noqa: E731
    assert new("5").verdict == "meets"
    assert new("6").verdict == "meets"
    assert new("4.5").verdict == "does_not_meet"   # closed list: below 5 fails
    # a low score entered as TOEFL iBT is read on the 0-120 scale: no longer sent to the university
    for score in ("5", "6", "80"):
        r = rep(slug, language=[{"test": "TOEFL iBT", "overall": score}], **base)["english"]
        assert r.verdict == "does_not_meet", score
    assert rep(slug, language=[{"test": "TOEFL PBT", "overall": "5"}], **base)["english"].verdict == "does_not_meet"
    # new-scale score without citizenship and study countries: an exception might still apply
    r = rep(slug, language=[{"test": "TOEFL iBT (2026 scale)", "overall": "4"}])["english"]
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")


@both
def test_degree_credits_german_degree_must_have_180_ects(slug):
    c = lambda **f: rep(slug, **f)["degree_credits"]  # noqa: E731
    assert c(degree_country="Germany", total_credits="180", credit_unit="ECTS").verdict == "meets"
    assert c(degree_country="Germany", total_credits="179", credit_unit="ECTS").verdict == "does_not_meet"
    assert c(degree_country="Germany", total_credits="180").verdict == "unknown"  # unit not stated
    # foreign degrees only need to be equivalent: a short total is never a fail
    assert c(degree_country="India", total_credits="150", credit_unit="ECTS").verdict == "unknown"
    assert c(degree_country="India", total_credits="180", credit_unit="ECTS").verdict == "meets"
    assert c(total_credits="150", credit_unit="ECTS").verdict == "unknown"  # country not given


@both
def test_aps_is_readiness_by_degree_country(slug):
    a = lambda **f: rep(slug, **f)["aps"]  # noqa: E731
    assert a(degree_country="Germany").verdict == "not_applicable"
    assert a(degree_country="India", documents=["aps_certificate"]).verdict == "meets"
    assert a(degree_country="Vietnam", documents=[]).verdict == "does_not_meet"
    assert a(degree_country="China").verdict == "unknown"
    assert a().verdict == "unknown"
    rules, _ = load_ruleset(load_settings(), slug)
    assert {r.id: r.category for r in rules.rules}["aps"] == "readiness"


@both
def test_headline_not_positive_while_the_university_decides(slug):
    p = Profile(degree_country="Germany", total_credits="180", credit_unit="ECTS",
                grade=grade("90", "100", "5"), language=[{"test": "IELTS", "overall": "7.5"}])
    r = check_eligibility(p, *load_ruleset(load_settings(), slug))
    by = {c.rule_id: c for c in r.criteria}
    assert [by[i].verdict for i in ("degree_credits", "grade_cgpa", "class_rank", "english")] == ["meets"] * 4
    assert by["degree_field"].reason == by["curricular_content"].reason == by["examination_board"].reason \
        == "university_review"
    assert by["branch_campus"].severity == "info"
    assert r.headline == "needs_information_or_review"


@both
def test_a_known_failure_gives_the_negative_headline(slug):
    p = Profile(grade=grade("60", "100", "5"))
    assert check_eligibility(p, *load_ruleset(load_settings(), slug)).headline == "does_not_meet_published_requirements"
