"""Explicit "no minimum published"
rules. They show in the trace as not_published, are informational, and never
move a headline or a count."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import Rule, RuleSet, load_ruleset, not_published_mismatches

CITE = {"doc_id": "de/x/y", "quote": "q"}
NP = {"type": "not_published", "note": "no minimum grade is published"}
PASS = {"type": "min", "fact": "total_credits", "value": "1"}


def test_not_published_must_be_informational():
    with pytest.raises(ValidationError, match="severity must be info"):
        Rule.model_validate({"id": "r", "label": "l", "check": NP, "citations": [CITE]})


def test_no_headline_or_count_effect():
    rs = RuleSet(slug="s", record_sha256="x", rules=[
        {"id": "a", "label": "credits", "check": PASS, "citations": [CITE], "reviewed_by": "human"},
        {"id": "g", "label": "grade", "severity": "info", "check": NP, "citations": [CITE], "reviewed_by": "human"},
    ])
    rep = check_eligibility(Profile(total_credits="1"), rs)
    assert rep.headline == "meets_checked_published_requirements"
    assert rep.admission.counts == {"meets": 1, "does_not_meet": 0, "unknown": 0, "not_published": 0}
    crit = rep.criteria[1]
    assert crit.verdict == "not_published" and crit.action == "No minimum is published: no minimum grade is published"


@pytest.mark.parametrize("slug,rule_id", [
    ("tu-berlin-m-sc-computer-science", "english_components"),
    ("kit-m-sc-computer-science", "min_grade"),
    ("kit-m-sc-computational-and-data-science", "gre_gate"),
])
def test_real_rules_are_backed_by_the_record(slug, rule_id):
    s = load_settings()
    rules, stale = load_ruleset(s, slug)
    record = json.loads((Path(s.paths.verified_dir) / f"{slug}.json").read_text())["record"]
    assert not stale and not_published_mismatches(rules, record) == []
    rule = next(r for r in rules.rules if r.id == rule_id)
    assert rule.severity == "info" and rule.reviewed_by == "human"
    rep = check_eligibility(Profile(), rules, stale)
    assert next(c for c in rep.criteria if c.rule_id == rule_id).verdict == "not_published"


def test_a_claim_the_record_contradicts_is_caught():
    rules, _ = load_ruleset(load_settings(), "kit-m-sc-computer-science")
    record = {"min_grade_german_scale": {"status": "stated", "value": "2.5"}}
    assert not_published_mismatches(rules, record) == ["min_grade"]



@pytest.mark.parametrize("check", [
    {"type": "all_of", "children": [PASS, NP]},
    {"type": "any_of", "children": [NP]},
    {"type": "when", "when": PASS, "then": NP},
    {"type": "when", "when": NP, "then": PASS},
])
def test_not_published_cannot_hide_inside_a_rule(check):
    with pytest.raises(ValidationError, match="never inside a group"):
        Rule.model_validate({"id": "r", "label": "l", "check": check, "citations": [CITE]})


def test_record_field_that_is_not_a_field_object_is_a_mismatch():
    rules, _ = load_ruleset(load_settings(), "kit-m-sc-computer-science")
    assert not_published_mismatches(rules, {"min_grade_german_scale": "text"}) == ["min_grade"]
