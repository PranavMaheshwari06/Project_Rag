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
def test_ds_gre_strict_bounds():
    assert ds(gre=gre())["gre"] == "meets"
    # failing GRE is never shown as a failure: EU/EEA citizens and German schooling are exempt (not built)
    for g in (gre(q="75"), gre(v="15"), gre(w="3.4")):
        assert ds(gre=g)["gre"] == "unknown"
    assert ds()["gre"] == "unknown"


def test_ds_never_exempt_on_citizenship_or_schooling():
    # the exemption is a university decision, not computed: an EU citizen without a GRE is not "meets"
    assert ds(citizenships=["Germany"])["gre"] == "unknown"
    assert ds(school_country="Germany")["gre"] == "unknown"
    assert ds(citizenships=["Germany"], school_country="Germany", gre=gre(q="1"))["gre"] == "unknown"
    # the CS country basis must not be reused here: a degree from an EU country does not exempt
    assert ds(degree_country="Germany")["gre"] == "unknown"


def test_ds_degree_and_profile_are_university_reviews():
    r = report(DS)
    status = {c.rule_id: (c.verdict, c.reason, c.severity) for c in r.criteria}
    assert status["degree"] == ("unknown", "university_review", "hard")
    assert status["module_profile"] == ("unknown", "university_review", "hard")
    assert {"degree", "module_profile", "gre", "english"} == set(status)   # no German rule: taught in English


def test_ds_english_is_an_admission_rule():
    rules, _ = load_ruleset(load_settings(), DS)
    assert {r.id: r.category for r in rules.rules}["english"] == "admission"


def test_ds_headline_never_positive_while_a_hard_review_remains():
    rep = report(DS, gre=gre(), degree_country="India", **ielts("7.5"))
    assert rep.headline == "needs_information_or_review"
    # a known failure elsewhere still wins over pending review: needs a rule that can fail, here none can for DS
    assert all(c.verdict != "does_not_meet" for c in rep.criteria)


def test_cs_headline_fails_on_known_gre_failure():
    assert report(CS, degree_country="India", gre=gre(q="40")).headline == "does_not_meet_published_requirements"


# --- Both: citations and review status ------------------------------------------
def test_rules_cite_the_verified_record_and_are_pending():
    s = load_settings()
    for slug in (CS, DS):
        rules, stale = load_ruleset(s, slug)
        record = json.loads((Path(s.paths.verified_dir) / f"{slug}.json").read_text())["record"]
        assert not stale
        assert all(r.reviewed_by == "pending" for r in rules.rules)
        # quotes the record omits must sit on cached HTML pages: the PDF cannot be re-checked from raw
        assert all(doc != "de/rwth/language-requirements-pdf" for _, doc, _ in uncited_quotes(rules, record))
