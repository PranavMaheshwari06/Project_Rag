"""Degree equivalence and
subject allocation stay hard university decisions, resolved only by the
university's assessment that the student reports for that programme."""

import pytest
from pydantic import ValidationError

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import SCHEMA_VERSION, Profile
from eligibility.rules import load_ruleset

TUB = "tu-berlin-m-sc-computer-science"
CDS = "kit-m-sc-computational-and-data-science"
RULES = {TUB: ("degree", "subject_allocation"), CDS: ("degree", "credit_counting")}


def verdicts(slug, assessments):
    rules, stale = load_ruleset(load_settings(), slug)
    rep = check_eligibility(Profile(university_assessments=assessments), rules, stale)
    return {c.rule_id: (c.verdict, c.reason) for c in rep.criteria if c.rule_id in RULES[slug]}


@pytest.mark.parametrize("slug", [TUB, CDS])
def test_one_assessment_resolves_both_rules(slug):
    assert set(verdicts(slug, None).values()) == {("unknown", "university_review")}
    assert set(verdicts(slug, {}).values()) == {("unknown", "university_review")}
    assert {v for v, _ in verdicts(slug, {slug: "positive"}).values()} == {"meets"}
    assert {v for v, _ in verdicts(slug, {slug: "negative"}).values()} == {"does_not_meet"}


def test_an_assessment_counts_only_for_its_own_programme():
    assert set(verdicts(CDS, {TUB: "positive"}).values()) == {("unknown", "university_review")}


@pytest.mark.parametrize("slug", [TUB, CDS])
def test_changed_rules_are_back_to_pending(slug):
    rules, _ = load_ruleset(load_settings(), slug)
    assert {r.id for r in rules.rules if r.id in RULES[slug] and r.reviewed_by == "pending"} == set(RULES[slug])


def test_profile_v5_and_values_are_closed():
    assert SCHEMA_VERSION == "profile-v5"  # introduced university_assessments
    with pytest.raises(ValidationError):
        Profile(university_assessments={TUB: "maybe"})



def test_no_assessment_keeps_the_university_note():
    rules, stale = load_ruleset(load_settings(), TUB)
    rep = check_eligibility(Profile(), rules, stale)
    degree = next(c for c in rep.criteria if c.rule_id == "degree")
    assert degree.action.startswith("The university decides: ") and "None" not in degree.action
