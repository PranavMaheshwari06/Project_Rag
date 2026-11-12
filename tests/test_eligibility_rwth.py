"""Real RWTH Aachen rule files: Computer Science and Data Science."""

import json
from pathlib import Path

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import load_ruleset, uncited_quotes

CS = "rwth-aachen-m-sc-computer-science"
DS = "rwth-aachen-m-sc-data-science"


def report(slug, **facts):
    return check_eligibility(Profile(**facts), *load_ruleset(load_settings(), slug))


def verdicts(slug, **facts):
    return {c.rule_id: c.verdict for c in report(slug, **facts).criteria}


def cs(**facts):
    return verdicts(CS, **facts)


def ds(**facts):
    return verdicts(DS, **facts)


def gre(q="76", v="16", w="3.5"):
    return {"quant_percentile": q, "verbal_percentile": v, "writing": w}


# --- Computer Science -----------------------------------------------------------
def test_cs_gre_strict_percentiles_and_inclusive_writing():
    india = {"degree_country": "India"}
    assert cs(**india, gre=gre())["gre"] == "meets"
    assert cs(**india, gre=gre(q="75"))["gre"] == "does_not_meet"   # "above the 75th": equality fails
    assert cs(**india, gre=gre(v="15"))["gre"] == "does_not_meet"   # "above the 15th": equality fails
    assert cs(**india, gre=gre(w="3.0"))["gre"] == "does_not_meet"
    assert cs(**india, gre=gre(w="3.5"))["gre"] == "meets"          # "at least 3.5"
    # scaled scores are a different fact: a perfect scaled score is not a percentile
    assert cs(**india, gre={"quant": "170", "verbal": "170", "writing": "6"})["gre"] == "unknown"


def test_cs_gre_unknown_vs_fail_and_country_basis():
    assert cs(degree_country="India")["gre"] == "unknown"            # needed, nothing given yet
    assert cs(degree_country="India", gre=gre(q="60"))["gre"] == "does_not_meet"
    assert cs(degree_country="Germany")["gre"] == "not_applicable"   # EU degree
    assert cs(degree_country="Ireland")["gre"] == "not_applicable"
    # the basis is the degree country: citizenship and school country never exempt
    assert cs(school_country="Germany", citizenships=["Germany"])["gre"] == "unknown"
    assert cs()["gre"] == "unknown"                                  # no degree country: never silently exempt
    assert cs(degree_country="United Kingdom")["gre"] == "unknown"   # not in the EU group
    assert cs(degree_country="Norway", gre=gre(q="10"))["gre"] == "does_not_meet"  # EEA is not the EU


def test_cs_german_is_readiness_at_c1():
    rep = report(CS, german_level="C1")
    c = {x.rule_id: x for x in rep.criteria}["german"]
    assert c.verdict == "meets"
    assert cs(german_level="C2")["german"] == "meets"
    assert cs(german_level="B2")["german"] == "unknown"   # exemptions may apply: never a failure
    assert cs()["german"] == "unknown"
    rules, _ = load_ruleset(load_settings(), CS)
    cat = {r.id: r.category for r in rules.rules}
    assert cat["german"] == cat["english"] == "readiness"


def ielts(overall):
    return {"language": [{"test": "IELTS", "overall": overall}]}


def test_english_routes_boundaries():
    for fn in (cs, ds):
        assert fn(**ielts("6.0"))["english"] == "meets"
        assert fn(**ielts("5.5"))["english"] == "unknown"   # RWTH may accept other proof: not a failure
        assert fn(language=[{"test": "TOEFL iBT", "overall": "90"}])["english"] == "meets"
        assert fn(language=[{"test": "TOEFL iBT", "overall": "89"}])["english"] == "unknown"
        assert fn(language=[{"test": "PTE Academic", "overall": "60"}])["english"] == "meets"
        assert fn(language=[{"test": "PTE Academic", "overall": "59"}])["english"] == "unknown"
        assert fn(language=[{"test": "FCE", "grade": "B"}])["english"] == "meets"
        assert fn(language=[{"test": "FCE", "grade": "C"}])["english"] == "unknown"  # B2 First needs B
        assert fn(language=[{"test": "CAE", "grade": "C"}])["english"] == "meets"
        assert fn(language=[{"test": "CPE", "grade": "C"}])["english"] == "meets"
        assert fn(language=[{"test": "UNIcert", "grade": "II"}])["english"] == "meets"
        assert fn(language=[{"test": "UNIcert", "grade": "I"}])["english"] == "unknown"
        assert fn()["english"] == "unknown"


def test_english_new_toefl_scale_is_a_separate_test():
    for fn in (cs, ds):
        new = lambda score: fn(language=[{"test": "TOEFL iBT (2026 scale)", "overall": score}])["english"]  # noqa: E731
        assert new("4.5") == "meets"
        assert new("6") == "meets"
        assert new("4.0") == "unknown"   # RWTH may accept other proof: not a failure
        # a new-scale score entered as TOEFL iBT is read on the 0-120 scale, never guessed
        assert fn(language=[{"test": "TOEFL iBT", "overall": "5"}])["english"] == "unknown"
    rules, _ = load_ruleset(load_settings(), DS)
    review = {r.id: r for r in rules.rules}["english"].check.children[-1]
    assert review.type == "university_review" and "4.5" not in review.note


def test_english_exemption_needs_a_known_country():
    for fn in (cs, ds):
        assert fn(degree_country="Canada")["english"] == "meets"
        assert fn(school_country="Australia")["english"] == "meets"
        assert fn(degree_country="India")["english"] == "unknown"
        assert fn(citizenships=["United States"])["english"] == "unknown"   # citizenship alone never exempts
        assert fn()["english"] == "unknown"


def test_cs_degree_is_the_examination_boards_call():
    rep = report(CS, degree_country="Germany", german_level="C1", **ielts("7.0"))
    assert rep.headline == "needs_information_or_review"
    assert rep.criteria[0].rule_id == "degree" and rep.criteria[0].reason == "university_review"


# --- Data Science ---------------------------------------------------------------
INDIAN = {"citizenships": ["India"], "school_country": "India"}   # known, not exempt


def test_ds_gre_strict_bounds_for_a_non_exempt_student():
    assert ds(**INDIAN, gre=gre())["gre"] == "meets"
    assert ds(**INDIAN, gre=gre(w="3.5"))["gre"] == "meets"          # "minimum score 3.5"
    for g in (gre(q="75"), gre(v="15"), gre(w="3.4")):                # "above": equality fails
        assert ds(**INDIAN, gre=g)["gre"] == "does_not_meet"
    # needed but no GRE entered: the normal missing-fact unknown, not a failure
    r = {c.rule_id: c for c in report(DS, **INDIAN).criteria}["gre"]
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")
    assert ds(**INDIAN, gre={})["gre"] == "unknown"


def test_ds_gre_exempt_by_eu_or_eea_citizenship():
    for country in ("Germany", "France", "Czechia", "Norway", "Iceland", "Liechtenstein"):
        assert ds(citizenships=[country], school_country="India")["gre"] == "not_applicable", country
        # exempt whatever the score, and whether or not the school country is known
        assert ds(citizenships=[country], gre=gre(q="1"))["gre"] == "not_applicable", country
    # one exempting citizenship is enough
    assert ds(citizenships=["India", "France"], school_country="India")["gre"] == "not_applicable"


def test_ds_gre_exempt_by_secondary_education_in_germany():
    assert ds(citizenships=["India"], school_country="Germany")["gre"] == "not_applicable"
    assert ds(school_country="Germany", gre=gre(q="1"))["gre"] == "not_applicable"   # citizenship not needed


def test_ds_gre_not_exempt_outside_the_eu_and_eea():
    # Switzerland and the UK are neither EU nor EEA: the GRE is needed
    for country in ("Switzerland", "United Kingdom", "India"):
        assert ds(citizenships=[country], school_country="India", gre=gre(q="60"))["gre"] == "does_not_meet"
    # the CS basis is not reused: a degree from an EU country does not exempt
    assert ds(**INDIAN, degree_country="Germany", gre=gre(q="60"))["gre"] == "does_not_meet"
    # "no citizenship" said explicitly is not an exemption
    assert ds(citizenships=[], school_country="India", gre=gre(q="60"))["gre"] == "does_not_meet"


def test_ds_gre_exemption_never_granted_on_unknown():
    assert ds()["gre"] == "unknown"
    assert ds(gre=gre(q="1"))["gre"] == "unknown"                          # condition unresolved, not a fail
    assert ds(citizenships=["India"])["gre"] == "unknown"                  # school country might be Germany
    assert ds(school_country="India")["gre"] == "unknown"                  # citizenship might be EU
    assert ds(degree_country="Germany")["gre"] == "unknown"
    r = {c.rule_id: c for c in report(DS, citizenships=["India"]).criteria}["gre"]
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")


def test_ds_degree_and_profile_are_university_reviews():
    r = report(DS)
    status = {c.rule_id: (c.verdict, c.reason, c.severity) for c in r.criteria}
    assert status["degree"] == ("unknown", "university_review", "hard")
    assert status["module_profile"] == ("unknown", "university_review", "hard")
    # no German rule: taught in English
    assert {"degree", "module_profile", "gre", "english", "deadline_winter", "deadline_summer"} == set(status)


def test_ds_english_is_an_admission_rule():
    rules, _ = load_ruleset(load_settings(), DS)
    assert {r.id: r.category for r in rules.rules}["english"] == "admission"


def test_ds_headline_never_positive_while_a_hard_review_remains():
    rep = report(DS, **INDIAN, gre=gre(), degree_country="India", **ielts("7.5"))
    assert rep.headline == "needs_information_or_review"
    assert all(c.verdict != "does_not_meet" for c in rep.criteria)
    # an exempt student is not held back by the GRE, but the hard reviews remain
    assert report(DS, citizenships=["Germany"], **ielts("7.5")).headline == "needs_information_or_review"


def test_ds_headline_fails_on_known_gre_failure():
    assert report(DS, **INDIAN, gre=gre(q="40")).headline == "does_not_meet_published_requirements"
    # the same score from an exempt student does not fail the headline
    assert report(DS, citizenships=["Norway"], gre=gre(q="40")).headline == "needs_information_or_review"


def test_cs_headline_fails_on_known_gre_failure():
    assert report(CS, degree_country="India", gre=gre(q="40")).headline == "does_not_meet_published_requirements"


# --- Both: citations and review status ------------------------------------------
def test_rules_cite_the_verified_record_and_are_reviewed():
    s = load_settings()
    for slug, pending in ((CS, {"deadline_winter", "deadline_summer"}), (DS, {"deadline_winter", "deadline_summer"})):
        rules, stale = load_ruleset(s, slug)
        record = json.loads((Path(s.paths.verified_dir) / f"{slug}.json").read_text())["record"]
        assert not stale
        assert {r.id for r in rules.rules if r.reviewed_by != "human"} == pending  # deadline rules drafted 2026-11-12, queued for the maintainer's review
        # quotes the record omits must sit on cached HTML pages: the PDF cannot be re-checked from raw
        assert all(doc != "de/rwth/language-requirements-pdf" for _, doc, _ in uncited_quotes(rules, record))
