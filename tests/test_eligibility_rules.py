"""Conditions (`when`), value matches (`in`) and the real TUM Informatics rules."""

import json
from pathlib import Path

from core.config import get_settings
from eligibility.engine import check_eligibility, evaluate
from eligibility.profile import Profile
from eligibility.rules import Rule, load_ruleset, uncited_quotes

CITE = {"doc_id": "de/x/y", "quote": "q"}
FROM_INDIA = {"type": "in", "fact": "degree_country", "values": ["India", "China"]}
TUM = "tum-m-sc-informatics"


def ev(check, **facts):
    rule = Rule.model_validate({"id": "r", "label": "l", "check": check, "citations": [CITE]})
    return evaluate(rule.check, Profile(**facts))


def test_in_is_case_insensitive_and_handles_lists_and_negation():
    assert ev(FROM_INDIA, degree_country="india").verdict == "meets"
    assert ev(FROM_INDIA, degree_country="Germany").verdict == "does_not_meet"
    assert ev(FROM_INDIA).verdict == "unknown"
    has_aps = {"type": "in", "fact": "documents", "values": ["aps_certificate"]}
    assert ev(has_aps, documents=["vpd", "aps_certificate"]).verdict == "meets"
    assert ev(has_aps, documents=[]).verdict == "does_not_meet"  # said none: a gap, not unknown
    abroad = {"type": "in", "fact": "degree_country", "values": ["Germany"], "negate": True}
    assert ev(abroad, degree_country="India").verdict == "meets"


def test_when_condition():
    gre = {"type": "when", "when": FROM_INDIA, "then": {"type": "min", "fact": "gre.quant", "value": "164"}}
    assert ev(gre, degree_country="Germany").verdict == "not_applicable"
    assert ev(gre, degree_country="India", gre={"quant": "163"}).verdict == "does_not_meet"
    # degree country not given: still unknown, never silently exempt
    r = ev(gre, gre={"quant": "170"})
    assert (r.verdict, r.reason) == ("unknown", "missing_fact")


def test_inactive_rules_do_not_count_in_groups_or_headline():
    off = {"type": "when", "when": FROM_INDIA, "then": {"type": "min", "fact": "total_credits", "value": "999"}}
    assert ev({"type": "all_of", "children": [off, off]}, degree_country="Germany").verdict == "not_applicable"
    from eligibility.rules import RuleSet
    rs = RuleSet(slug="s", record_sha256="x", rules=[
        {"id": "a", "label": "a", "check": off, "citations": [CITE], "reviewed_by": "human"},
        {"id": "b", "label": "b", "check": {"type": "min", "fact": "total_credits", "value": "1"},
         "citations": [CITE], "reviewed_by": "human"}])
    rep = check_eligibility(Profile(degree_country="Germany", total_credits="10"), rs)
    assert rep.headline == "meets_checked_published_requirements"


def tum_report(**facts):
    return {c.rule_id: c for c in check_eligibility(Profile(**facts), *load_ruleset(get_settings(), TUM)).criteria}


def test_tum_gre_or_gate():
    india = {"degree_country": "India"}
    assert tum_report(**india, gre={"quant": "164", "writing": "4.0"})["gre_or_gate"].verdict == "meets"
    low_gre = {"quant": "163", "writing": "5"}
    # GRE fails but GATE was not supplied: the other route is still open
    assert tum_report(**india, gre=low_gre)["gre_or_gate"].verdict == "unknown"
    assert tum_report(**india, gre=low_gre, gate={"paper": "CS", "qualified": False})["gre_or_gate"].verdict \
        == "does_not_meet"
    # GRE writing too low, but a qualifying GATE CS scorecard is the alternative route
    assert tum_report(**india, gre={"quant": "170", "writing": "3.5"},
                      gate={"paper": "CS", "qualified": True})["gre_or_gate"].verdict == "meets"
    # GATE in another paper does not count for Informatics
    assert tum_report(**india, gre=low_gre, gate={"paper": "ME", "qualified": True})["gre_or_gate"].verdict \
        == "does_not_meet"
    assert tum_report(degree_country="Germany")["gre_or_gate"].verdict == "not_applicable"
    assert tum_report(gre={"quant": "170", "writing": "5"})["gre_or_gate"].verdict == "unknown"


def test_tum_never_positive_while_university_decides():
    rep = check_eligibility(Profile(degree_country="Germany"), *load_ruleset(get_settings(), TUM))
    assert rep.headline == "needs_information_or_review"
    assert rep.criteria[0].reason == "university_review"


def test_tum_rules_cite_the_verified_record():
    s = get_settings()
    rules, stale = load_ruleset(s, TUM)
    record = json.loads((Path(s.paths.verified_dir) / f"{TUM}.json").read_text())["record"]
    assert not stale
    # only the English rule cites evidence the record omits (english is not_published there)
    assert {r for r, _, _ in uncited_quotes(rules, record)} == {"english"}
    rules.rules[0].citations[0].quote = "a quote that is on no page"
    assert {r for r, _, _ in uncited_quotes(rules, record)} == {"degree", "english"}


def lang(*entries):
    return {"language": list(entries)}


def test_tum_english_alternatives():
    eng = lambda **f: tum_report(**f)["english"]  # noqa: E731
    assert eng(**lang({"test": "IELTS", "overall": "6.5"})).verdict == "meets"
    assert eng(**lang({"test": "toefl ibt", "overall": "88"})).verdict == "meets"  # name match ignores case
    assert eng(**lang({"test": "PTE Academic", "overall": "64"}), english_instruction_share="50").verdict == "meets"
    assert eng(**lang({"test": "CAE", "grade": "B"})).verdict == "meets"
    assert eng(english_instruction_share="50").verdict == "meets"  # exactly half counts
    # failing every listed route is still unknown: TUM may accept other proof, so we never say fails
    r = eng(**lang({"test": "IELTS", "overall": "6.0"}), english_instruction_share="40")
    assert (r.verdict, r.reason) == ("unknown", "university_review")
    # nothing supplied: unknown, and asking for the missing fact
    assert eng().verdict == "unknown"


def test_tum_english_rule_waits_for_maintainer_review():
    rules, _ = load_ruleset(get_settings(), TUM)
    status = {r.id: r.reviewed_by for r in rules.rules}
    assert status["english"] == "pending"  # new interpretation, not yet accepted
    assert status["gre_or_gate"] == status["degree"] == status["aptitude_assessment"] == "human"
