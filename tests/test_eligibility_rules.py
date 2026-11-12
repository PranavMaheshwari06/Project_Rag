"""Conditions (`when`), value matches (`in`) and the real TUM Informatics rules."""

import json
from pathlib import Path

from core.config import load_settings
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
    return {c.rule_id: c for c in check_eligibility(Profile(**facts), *load_ruleset(load_settings(), TUM)).criteria}


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
    rep = check_eligibility(Profile(degree_country="Germany"), *load_ruleset(load_settings(), TUM))
    assert rep.headline == "needs_information_or_review"
    assert rep.criteria[0].reason == "university_review"


def test_tum_rules_cite_the_verified_record():
    s = load_settings()
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


def test_tum_review_status():
    rules, _ = load_ruleset(load_settings(), TUM)
    status = {r.id: r.reviewed_by for r in rules.rules}
    # every rule is human-reviewed, including the readiness rules aps and vpd (R16) and the
    # deadline rules (accepted 2026-11-13)
    assert {k for k, v in status.items() if v != "human"} == set()


# --- KIT Computer Science -------------------------------------------------------
KIT = "kit-m-sc-computer-science"


def kit(**facts):
    return {c.rule_id: c for c in check_eligibility(Profile(**facts), *load_ruleset(load_settings(), KIT)).criteria}


FULL = {"theoretical_cs": "15", "practical_cs": "30", "computer_engineering": "8", "mathematics": "25"}


def test_kit_selection_routes_are_alternatives():
    entry = lambda **f: kit(**f)["selection_entry"]  # noqa: E731
    assert entry(subject_credits=FULL).verdict == "meets"                    # credit route, exact minimums
    assert entry(subject_credits={**FULL, "mathematics": "24"}).verdict == "unknown"  # GATE not supplied: still open
    assert entry(gate={"paper": "DA", "qualified": True}).verdict == "meets"  # GATE alone is enough
    assert entry(gate={"paper": "ME", "qualified": True}).verdict == "unknown"  # wrong paper, other routes open
    # credits short and GATE failed, but the interview route has no rank/interview facts yet
    short = {**FULL, "mathematics": "24"}
    assert entry(subject_credits=short, gate={"paper": "CS", "qualified": False}).verdict == "unknown"


def test_kit_interview_route():
    entry = lambda **f: kit(**f)["selection_entry"]  # noqa: E731
    relaxed = {"theoretical_cs": "15", "practical_cs": "20", "computer_engineering": "6", "mathematics": "20"}
    top10 = {"obtained": "9", "best": "10", "passing": "5", "class_rank_percentile": "10"}
    no_gate = {"paper": "CS", "qualified": False}
    base = {"gate": no_gate, "grade": top10}
    # prerequisites met, interview not taken yet: invited, not passed
    assert entry(subject_credits=relaxed, **base).verdict == "unknown"
    assert entry(subject_credits=relaxed, interview_passed=True, **base).verdict == "meets"
    assert entry(subject_credits=relaxed, interview_passed=False, **base).verdict == "does_not_meet"
    # three of four areas is enough: computer engineering below the relaxed minimum
    three = {**relaxed, "computer_engineering": "5"}
    assert entry(subject_credits=three, interview_passed=True, **base).verdict == "meets"
    # only two areas reach the relaxed minimums
    two = {**three, "mathematics": "19"}
    assert entry(subject_credits=two, interview_passed=True, **base).verdict == "does_not_meet"
    # top 10% is strict about the rank: 11% fails the route
    rank11 = {**top10, "class_rank_percentile": "11"}
    assert entry(subject_credits=relaxed, interview_passed=True, gate=no_gate, grade=rank11).verdict == "does_not_meet"


def test_kit_credits_need_ects():
    ects = lambda **f: kit(**f)["degree_ects"]  # noqa: E731
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


def test_kit_gre_depends_on_the_degree_country():
    gre = lambda country, **f: kit(degree_country=country, **f)["gre_or_gate"]  # noqa: E731
    scores = {"verbal": "151", "quant": "164", "writing": "4"}
    assert gre("India", gre=scores).verdict == "meets"                           # not exempt: scores needed, met
    low = {**scores, "quant": "163"}
    assert gre("India", gre=low).verdict == "unknown"                            # GATE route still open
    assert gre("India", gre=low, gate={"paper": "CS", "qualified": False}).verdict == "does_not_meet"
    assert gre("India", gate={"paper": "CS", "qualified": True}).verdict == "meets"  # GATE replaces the GRE
    assert gre("Germany").verdict == "not_applicable"                            # EHEA
    assert gre("Canada").verdict == "not_applicable"                             # Lisbon only
    assert gre("Russia").verdict == "not_applicable"                             # EHEA-suspended, but Lisbon ratified
    assert gre("United States").verdict == "unknown"                             # signed, not ratified
    assert gre("India").verdict == "unknown"                                     # needed, no result given yet
    assert kit()["gre_or_gate"].verdict == "unknown"                             # no degree country at all
    assert kit()["test_validity"].verdict == "unknown"                           # age limits not modelled yet


def test_kit_english_routes():
    eng = lambda **f: kit(**f)["english"]  # noqa: E731
    def ielts(writing):
        return {"test": "IELTS", "overall": "6.5",
                "components": {"Listening": "6", "Reading": "6", "Speaking": "6", "Writing": writing}}

    assert eng(language=[{"test": "TOEFL iBT", "overall": "90"}]).verdict == "meets"
    assert eng(language=[ielts("5.5")]).verdict == "meets"
    # a section below 5.5 fails IELTS, but other KIT-accepted proof may exist: unknown, never a fail
    assert eng(language=[ielts("5.0")]).verdict == "unknown"
    assert eng(language=[{"test": "CAE", "grade": "pass"}]).verdict == "meets"
    assert eng(english_instruction_share="100").verdict == "meets"
    assert eng(english_instruction_share="90").verdict == "unknown"  # "sole language" means all of it


def test_kit_headline_never_positive_while_the_university_decides():
    p = Profile(subject_credits=FULL, total_credits="180", credit_unit="ECTS",
                language=[{"test": "TOEFL iBT", "overall": "95"}])
    rep = check_eligibility(p, *load_ruleset(load_settings(), KIT))
    assert rep.headline == "needs_information_or_review"
    info = [c for c in rep.criteria if c.rule_id == "module_assignment"][0]
    assert info.severity == "info"  # shown, but never part of the headline
