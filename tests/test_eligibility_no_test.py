"""A student can say they have no GRE or no GATE. `None` (and an empty `Gre()`)
stays "unknown"; "none" makes a score bound fail as "not reported". Scores are
compared exactly as before."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.config import load_settings
from eligibility.engine import check_eligibility, evaluate
from eligibility.profile import SCHEMA_VERSION, Profile
from eligibility.rules import Rule, load_ruleset

CITE = {"doc_id": "de/x/y", "quote": "q"}
QUANT = {"type": "min", "fact": "gre.quant", "value": "164"}
GATE_OK = {"type": "in", "fact": "gate.qualified", "values": [True]}
EITHER = {"type": "any_of", "children": [QUANT, GATE_OK]}


def ev(check, **facts):
    rule = Rule.model_validate({"id": "r", "label": "l", "check": check, "citations": [CITE]})
    return evaluate(rule.check, Profile(**facts))


def test_schema_version_bumped_and_none_round_trips():
    # profile-v2 introduced "none"; later versions keep it
    assert SCHEMA_VERSION in ("profile-v2", "profile-v3") and Profile().schema_version == SCHEMA_VERSION
    p = Profile(gre="none", gate="none")
    back = Profile.model_validate_json(p.model_dump_json())
    assert back == p and back.gre == "none" and back.gate == "none"
    assert json.loads(p.model_dump_json())["gre"] == "none"


def test_v1_profile_still_loads():
    old = {"schema_version": "profile-v1", "gre": {"quant": "165"}, "gate": {"paper": "CS"}}
    assert Profile.model_validate(old).gre.quant == 165


@pytest.mark.parametrize("bad", ["None", "no", "", "NONE", False, 0])
def test_only_the_literal_none_means_no_test(bad):
    with pytest.raises(ValidationError):
        Profile(gre=bad)
    with pytest.raises(ValidationError):
        Profile(gate=bad)


def test_unknown_schema_version_rejected():
    with pytest.raises(ValidationError):
        Profile(schema_version="profile-v9")


def test_not_supplied_and_empty_stay_unknown():
    for gre in (None, {}):
        r = ev(QUANT, gre=gre)
        assert r.verdict == "unknown" and r.reason == "missing_fact"


def test_none_fails_a_bound_as_not_reported():
    r = ev(QUANT, gre="none")
    assert r.verdict == "does_not_meet" and r.entered == "not reported" and r.margin is None
    assert ev(GATE_OK, gate="none").verdict == "does_not_meet"
    assert ev({"type": "in", "fact": "gate.paper", "values": ["CS"]}, gate="none").verdict == "does_not_meet"


def test_scores_unchanged():
    assert ev(QUANT, gre={"quant": "164"}).verdict == "meets"
    assert ev(QUANT, gre={"quant": "163"}).margin == -1


def test_alternatives_with_no_test():
    assert ev(EITHER, gre="none", gate="none").verdict == "does_not_meet"
    assert ev(EITHER, gre="none").verdict == "unknown"  # GATE not supplied: still possible
    assert ev(EITHER, gre="none", gate={"qualified": True}).verdict == "meets"
    assert ev(EITHER, gre={"quant": "170"}, gate="none").verdict == "meets"


def test_kit_cs_gre_or_gate_with_no_tests():
    settings = load_settings()
    rules, stale = load_ruleset(settings, "kit-m-sc-computer-science")

    def verdict(**facts):
        rep = check_eligibility(Profile(degree_country="India", **facts), rules, stale)
        return next(c for c in rep.criteria if c.rule_id == "gre_or_gate").verdict

    assert verdict(gre="none", gate="none") == "does_not_meet"
    assert verdict(gre="none") == "unknown"
    assert verdict() == "unknown"
    # a degree country exempt from the test: "none" does not matter
    rep = check_eligibility(Profile(degree_country="Germany", gre="none", gate="none"), rules, stale)
    assert next(c for c in rep.criteria if c.rule_id == "gre_or_gate").verdict == "not_applicable"


def test_empty_gate_stays_unknown():
    assert ev(GATE_OK, gate={}).verdict == "unknown"


def test_negated_check_on_a_test_the_student_does_not_have_is_met():
    not_cs = {"type": "in", "fact": "gate.paper", "values": ["CS"], "negate": True}
    assert ev(not_cs, gate="none").verdict == "meets"
    # so a requirement keyed on "no qualifying GATE" applies instead of being skipped
    when = {"type": "when", "when": {"type": "in", "fact": "gate.qualified", "values": [True], "negate": True},
            "then": QUANT}
    assert ev(when, gate="none", gre="none").verdict == "does_not_meet"


def test_a_misspelled_path_still_fails_loudly_with_none():
    with pytest.raises(ValueError, match="unknown profile fact"):
        ev({"type": "min", "fact": "gre.qaunt", "value": "1"}, gre="none")
    with pytest.raises(ValueError, match="unknown profile fact"):
        ev({"type": "in", "fact": "degree_country.code", "values": ["x"]}, degree_country="none")


def test_none_in_other_fields_is_a_plain_value():
    assert ev({"type": "in", "fact": "degree_country", "values": ["none"]}, degree_country="none").verdict == "meets"


def test_v1_profile_cannot_say_none():
    with pytest.raises(ValidationError, match="profile-v2"):
        Profile(schema_version="profile-v1", gre="none")


def test_not_reported_reaches_group_criteria_and_report_has_profile_version():
    settings = load_settings()
    rules, stale = load_ruleset(settings, "kit-m-sc-computer-science")
    rep = check_eligibility(Profile(degree_country="India", gre="none", gate="none"), rules, stale)
    crit = next(c for c in rep.criteria if c.rule_id == "gre_or_gate")
    assert crit.entered == "not reported"
    assert rep.profile_schema_version == SCHEMA_VERSION


RULE_FILES = sorted(p.stem for p in Path(load_settings().paths.rules_dir).glob("*.json"))


@pytest.mark.parametrize("slug", RULE_FILES)
@pytest.mark.parametrize("country", ["India", "China", "Germany", "United States", None])
def test_none_never_helps_in_a_real_rule_file(slug, country):
    """Saying "none" may only turn unknown into does_not_meet, never into a pass or an exemption."""
    settings = load_settings()
    rules, stale = load_ruleset(settings, slug)
    before = check_eligibility(Profile(degree_country=country), rules, stale).criteria
    after = check_eligibility(Profile(degree_country=country, gre="none", gate="none"), rules, stale).criteria
    for b, a in zip(before, after):
        assert a.verdict == b.verdict or (b.verdict, a.verdict) == ("unknown", "does_not_meet"), (slug, b.rule_id)
