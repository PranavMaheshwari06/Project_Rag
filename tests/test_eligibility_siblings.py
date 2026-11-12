"""Real rule files: TUM Data Engineering and Analytics and KIT Computational and Data Science."""

import json
from pathlib import Path

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import load_ruleset, uncited_quotes

DEA = "tum-m-sc-data-engineering-and-analytics"
CDS = "kit-m-sc-computational-and-data-science"


def report(slug, **facts):
    return {c.rule_id: c for c in check_eligibility(Profile(**facts), *load_ruleset(load_settings(), slug)).criteria}


def dea(**facts):
    return report(DEA, **facts)


def cds(**facts):
    return report(CDS, **facts)


def test_files_are_fresh_reviewed_and_cite_the_record():
    s = load_settings()
    deadlines = {"deadline_winter", "deadline_summer"}
    for slug, outside, pending in (
        (DEA, {"english", "aptitude_assessment"}, deadlines),  # DEA deadlines drafted 2026-11-12, queued
        (CDS, {"credit_minimums", "english"} | deadlines, set()),
    ):
        rules, stale = load_ruleset(s, slug)
        record = json.loads((Path(s.paths.verified_dir) / f"{slug}.json").read_text())["record"]
        assert not stale
        assert {r.id for r in rules.rules if r.reviewed_by != "human"} == pending
        # only evidence the record omits may be cited from the cached page instead
        assert {r for r, _, _ in uncited_quotes(rules, record)} <= outside


# --- TUM Data Engineering and Analytics --------------------------------------------
def test_dea_gre_or_gate():
    india = {"degree_country": "India"}
    assert dea(**india, gre={"quant": "164", "writing": "4.0"})["gre_or_gate"].verdict == "meets"
    low = {"quant": "163", "writing": "5"}
    assert dea(**india, gre={"quant": "170", "writing": "3.9"})["gre_or_gate"].verdict == "unknown"  # GATE still open
    assert dea(**india, gre=low)["gre_or_gate"].verdict == "unknown"
    assert dea(**india, gre=low, gate={"paper": "CS", "qualified": False})["gre_or_gate"].verdict == "does_not_meet"
    assert dea(**india, gre=low, gate={"paper": "CS", "qualified": True})["gre_or_gate"].verdict == "meets"
    # only the CS paper counts; the CSE-only Mechanical Engineering exception is not copied
    assert dea(**india, gre=low, gate={"paper": "ME", "qualified": True})["gre_or_gate"].verdict == "does_not_meet"
    for country in ("Bangladesh", "China", "Iran", "Pakistan"):
        assert dea(degree_country=country, gre=low, gate={"paper": "CS", "qualified": False})["gre_or_gate"].verdict \
            == "does_not_meet"
    assert dea(degree_country="Germany")["gre_or_gate"].verdict == "not_applicable"
    # never exempt on unknown: no degree country, even with a failing GRE
    r = dea(gre=low)["gre_or_gate"]
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")
    assert dea()["gre_or_gate"].verdict == "unknown"


def test_dea_english_routes():
    eng = lambda **f: dea(**f)["english"]  # noqa: E731
    assert eng(language=[{"test": "IELTS", "overall": "6.5"}]).verdict == "meets"
    assert eng(language=[{"test": "TOEFL iBT", "overall": "88"}]).verdict == "meets"
    assert eng(language=[{"test": "PTE Academic", "overall": "65"}]).verdict == "meets"
    assert eng(language=[{"test": "CPE", "grade": "C"}]).verdict == "meets"
    assert eng(english_instruction_share="50").verdict == "meets"
    # every listed route fails: still unknown, TUM may accept other proof
    r = eng(language=[{"test": "IELTS", "overall": "6.0"}, {"test": "TOEFL iBT", "overall": "87"}],
            english_instruction_share="49")
    assert (r.verdict, r.reason) == ("unknown", "university_review")
    assert eng().verdict == "unknown"


def test_dea_readiness_conditions_are_never_silently_exempt():
    assert dea(degree_country="India", documents=[])["aps"].verdict == "does_not_meet"
    assert dea(degree_country="India", documents=["aps_certificate"])["aps"].verdict == "meets"
    assert dea(degree_country="Vietnam")["aps"].verdict == "unknown"  # country listed, documents not supplied
    assert dea(degree_country="Germany")["aps"].verdict == "not_applicable"
    assert dea(documents=[])["aps"].verdict == "unknown"  # degree country missing
    assert dea(degree_country="Germany")["vpd"].verdict == "not_applicable"
    assert dea(degree_country="India", documents=["aps_certificate"])["vpd"].verdict == "does_not_meet"
    assert dea(documents=["vpd"])["vpd"].verdict == "unknown"
    rules, _ = load_ruleset(load_settings(), DEA)
    assert {r.id: r.category for r in rules.rules}["aps"] == "readiness"


def test_dea_headline_not_positive_while_the_university_decides():
    p = Profile(degree_country="Germany", language=[{"test": "IELTS", "overall": "7"}])
    rep = check_eligibility(p, *load_ruleset(load_settings(), DEA))
    assert rep.headline == "needs_information_or_review"
    by_id = {c.rule_id: c for c in rep.criteria}
    assert by_id["degree"].reason == by_id["aptitude_assessment"].reason == "university_review"


# --- KIT Computational and Data Science --------------------------------------------
FULL = {"basic_mathematics": "20", "bachelor_thesis": "6", "applied_mathematics": "40",
        "computer_science": "12", "science_engineering_economics": "12"}


def credits(**over):
    return cds(subject_credits={**FULL, **over})["credit_minimums"]


def test_cds_credit_minimums_boundaries():
    assert credits().verdict == "meets"
    # any of the three areas can be the one with 40 credits
    assert credits(applied_mathematics="12", computer_science="40").verdict == "meets"
    assert credits(applied_mathematics="12", science_engineering_economics="40").verdict == "meets"
    # one credit short anywhere: not an unconditional pass, but conditional admission is possible
    for short in ({"basic_mathematics": "19"}, {"bachelor_thesis": "5"}, {"science_engineering_economics": "11"},
                  {"applied_mathematics": "39"}):
        r = credits(**short)
        assert (r.verdict, r.reason) == ("unknown", "university_review"), short
    assert credits(computer_science="39", applied_mathematics="12", science_engineering_economics="12") \
        .verdict == "unknown"


def test_cds_far_below_the_minimums_fails():
    # a single shortfall above 12 credits cannot be covered by conditional admission
    assert credits(basic_mathematics="8").verdict == "unknown"        # exactly 12 short
    assert credits(basic_mathematics="7").verdict == "does_not_meet"  # 13 short
    assert credits(basic_mathematics="0").verdict == "does_not_meet"
    none_big = {"applied_mathematics": "27", "computer_science": "27", "science_engineering_economics": "27"}
    assert credits(**none_big).verdict == "does_not_meet"  # no area within 12 of 40
    assert credits(**{**none_big, "computer_science": "28"}).verdict == "unknown"


def test_cds_unknown_is_not_a_failure():
    assert cds()["credit_minimums"].verdict == "unknown"
    assert cds(subject_credits={})["credit_minimums"].verdict == "unknown"
    # thesis credits not given: cannot pass outright, never reported as failed
    part = {k: v for k, v in FULL.items() if k != "bachelor_thesis"}
    assert cds(subject_credits=part)["credit_minimums"].verdict == "unknown"
    # said "none" is a known zero, not missing
    assert credits(bachelor_thesis="0").verdict == "unknown"  # 6 short is inside the 12-credit window
    assert cds(subject_credits={"basic_mathematics": "0"})["credit_minimums"].verdict == "does_not_meet"


def test_cds_counting_policy_is_a_hard_university_decision():
    c = cds(subject_credits=FULL)["credit_counting"]
    assert (c.verdict, c.reason, c.severity) == ("unknown", "university_review", "hard")
    assert cds(subject_credits=FULL)["degree"].reason == "university_review"


def test_cds_credits_need_ects():
    ects = lambda **f: cds(**f)["degree_ects"]  # noqa: E731
    assert ects(total_credits="180", credit_unit="ECTS").verdict == "meets"
    assert ects(total_credits="179", credit_unit="ECTS").verdict == "does_not_meet"
    assert ects(total_credits="170", credit_unit="ECTS").verdict == "does_not_meet"
    assert ects(credit_unit="ECTS").verdict == "unknown"  # total not stated
    # another unit is not converted: KIT decides (X3), never a fail, whatever the number
    for unit in ("other",):  # profile-v4: the unit is a closed choice
        for total in ("240", "120"):
            r = ects(total_credits=total, credit_unit=unit)
            assert (r.verdict, r.reason) == ("unknown", "university_review"), (unit, total)
    r = ects(total_credits="180")  # unit not stated
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")


def test_cds_english_routes_and_no_gre():
    eng = lambda **f: cds(**f)["english"]  # noqa: E731

    def ielts(writing, overall="6.5"):
        return {"test": "IELTS", "overall": overall,
                "components": {"Listening": "6", "Reading": "6", "Speaking": "6", "Writing": writing}}

    assert eng(language=[{"test": "TOEFL iBT", "overall": "90"}]).verdict == "meets"
    assert eng(language=[ielts("5.5")]).verdict == "meets"
    assert eng(language=[ielts("5.0")]).verdict == "unknown"          # section below 5.5, other proof may exist
    assert eng(language=[ielts("6", overall="6.0")]).verdict == "unknown"
    assert eng(language=[{"test": "FCE", "grade": "B"}]).verdict == "meets"
    assert eng(english_instruction_share="100").verdict == "meets"
    assert eng(english_instruction_share="99").verdict == "unknown"   # "sole language" means all of it
    assert eng().verdict == "unknown"
    assert "gre_or_gate" not in cds()  # KIT publishes no entrance test for this programme


def test_cds_headline_not_positive_while_the_university_decides():
    p = Profile(subject_credits=FULL, total_credits="180", credit_unit="ECTS",
                language=[{"test": "TOEFL iBT", "overall": "95"}])
    rep = check_eligibility(p, *load_ruleset(load_settings(), CDS))
    assert rep.headline == "needs_information_or_review"
    far = Profile(subject_credits={**FULL, "basic_mathematics": "0"})
    assert check_eligibility(far, *load_ruleset(load_settings(), CDS)).headline == "does_not_meet_published_requirements"
