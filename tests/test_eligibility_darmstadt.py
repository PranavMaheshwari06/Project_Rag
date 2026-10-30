"""TU Darmstadt English-taught master's rule files (Computer Science, AI and Machine Learning)."""

import pytest

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import load_ruleset

CS = "tu-darmstadt-m-sc-computer-science"
AIML = "tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning"
BOTH = pytest.mark.parametrize("slug", [CS, AIML])


def report(slug, **facts):
    return check_eligibility(Profile(**facts), *load_ruleset(load_settings(), slug))


def crit(slug, **facts):
    return {c.rule_id: c for c in report(slug, **facts).criteria}


GOOD_GRE = {"verbal": "155", "quant": "165", "writing": "3.5"}


@BOTH
def test_core_courses_boundary(slug):
    core = lambda v: crit(slug, subject_credits={"core_courses": v})["core_courses"].verdict  # noqa: E731
    assert core("60") == "meets"
    assert core("59.5") == "does_not_meet"  # partial overlaps count proportionally, so halves exist
    assert crit(slug)["core_courses"].verdict == "unknown"
    assert crit(slug, subject_credits={"mathematics": "30"})["core_courses"].verdict == "unknown"


@BOTH
def test_180_ects_and_other_units(slug):
    ects = lambda **f: crit(slug, **f)["degree_ects"].verdict  # noqa: E731
    assert ects(total_credits="180", credit_unit="ECTS") == "meets"
    assert ects(total_credits="179", credit_unit="ECTS") == "does_not_meet"
    assert ects(total_credits="180") == "unknown"  # unit not stated
    # not ECTS: "equivalent workload" is the university's call, never a fail
    assert ects(total_credits="240", credit_unit="US credits") == "unknown"
    assert ects(total_credits="120", credit_unit="US credits") == "unknown"


@BOTH
def test_gre_boundaries_each_part_binding(slug):
    ex = lambda **g: crit(slug, gre=g)["entrance_exam"]  # noqa: E731
    assert ex(**GOOD_GRE).verdict == "meets"
    # one part short: no compensation, but the university may still exempt or test: unknown, not a fail
    for part, low in (("verbal", "154"), ("quant", "164"), ("writing", "3.0")):
        assert ex(**{**GOOD_GRE, part: low}).verdict == "unknown"
    assert ex(**{**GOOD_GRE, "verbal": "170", "quant": "164"}).verdict == "unknown"  # high verbal cannot compensate


@BOTH
def test_never_exempt_on_unknown(slug):
    # a part missing (not zero) is not an exemption
    assert crit(slug, gre={"verbal": "160", "quant": "170"})["entrance_exam"].verdict == "unknown"
    assert crit(slug)["entrance_exam"].verdict == "unknown"
    # GATE alone is not modelled (no GATE score fact): a qualified scorecard does not exempt silently
    assert crit(slug, gate={"paper": "CS", "qualified": True})["entrance_exam"].verdict == "unknown"


@BOTH
def test_english_alternatives(slug):
    eng = lambda **f: crit(slug, **f)["english"].verdict  # noqa: E731

    def ielts(v):
        return {"language": [{"test": "IELTS", "overall": v}]}

    assert eng(**ielts("7.0")) == "meets"
    assert eng(**ielts("6.5")) == "unknown"  # other routes (TOEFL, English-taught degree) not yet ruled out
    assert eng(**{"language": [{"test": "TOEFL iBT", "overall": "95"}]}) == "meets"
    assert eng(**{"language": [{"test": "TOEFL iBT", "overall": "94"}]}) == "unknown"
    assert eng(english_instruction_share="100") == "meets"
    assert eng(english_instruction_share="99") == "unknown"
    # every published route failed
    assert eng(language=[{"test": "IELTS", "overall": "6.5"}, {"test": "TOEFL iBT", "overall": "90"}],
               english_instruction_share="80") == "does_not_meet"
    assert eng() == "unknown"


@BOTH
def test_headline_never_positive_while_a_hard_review_remains(slug):
    p = dict(total_credits="180", credit_unit="ECTS", subject_credits={"core_courses": "90"},
             gre=GOOD_GRE, language=[{"test": "IELTS", "overall": "8"}])
    rep = report(slug, **p)
    v = {c.rule_id: c.verdict for c in rep.criteria}
    assert v["degree_ects"] == v["core_courses"] == v["entrance_exam"] == v["english"] == "meets"
    assert v["degree"] == v["core_courses_match"] == "unknown"
    assert rep.headline == "needs_information_or_review"


@BOTH
def test_a_known_failure_still_shows_in_the_headline(slug):
    rep = report(slug, subject_credits={"core_courses": "30"})
    assert rep.headline == "does_not_meet_published_requirements"


def test_rules_are_pending_and_all_hard():
    for slug in (CS, AIML):
        rules, stale = load_ruleset(load_settings(), slug)
        assert not stale
        assert {r.reviewed_by for r in rules.rules} == {"pending"}
        assert {r.severity for r in rules.rules} == {"hard"}
