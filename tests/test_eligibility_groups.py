"""Country groups: counts match the official pages, three-way membership, notices."""

from datetime import date

import pytest

from core.config import get_settings
from eligibility.engine import check_eligibility, default_groups, evaluate
from eligibility.groups import load_groups
from eligibility.profile import Profile
from eligibility.rules import Rule, RuleSet

CITE = {"doc_id": "de/x/y", "quote": "q"}


def groups():
    return default_groups()


def test_counts_match_the_official_pages_read_on_2026_10_29():
    g = groups().groups
    assert (len(g["EHEA"].members), len(g["LISBON"].members), len(g["EU"].members)) == (49, 57, 27)
    assert all(x.reviewed_by == "human" for x in g.values())


def test_lists_are_internally_consistent():
    g = groups().groups
    for grp in g.values():
        assert len(set(grp.members)) == len(grp.members)
        assert set(grp.uncertain) <= set(grp.members) or grp is g["LISBON"]  # US is signed-only, not a member
    assert set(g["EU"].members) <= set(g["EHEA"].members) & set(g["LISBON"].members)
    assert not set(g["LISBON"].uncertain) & set(g["LISBON"].members)


@pytest.mark.parametrize("group,country,expected", [
    ("EHEA", "Germany", "member"), ("EHEA", "germany ", "member"),
    ("EHEA", "Czechia", "member"), ("EHEA", "Turkey", "member"),       # alias names
    ("EHEA", "Russia", "uncertain"), ("EHEA", "Belarus", "uncertain"),
    ("EHEA", "India", "no"), ("EHEA", "Canada", "no"),
    ("LISBON", "Canada", "member"), ("LISBON", "Russia", "member"),
    ("LISBON", "USA", "uncertain"), ("LISBON", "India", "no"),
    ("EU", "Poland", "member"), ("EU", "Switzerland", "no"), ("EU", "Norway", "no"),
    ("EHEA", "Atlantis", "no"),                                           # unknown name: not exempt
])
def test_membership(group, country, expected):
    assert groups().membership(group, country) == expected


def exempt(values, country):
    check = {"type": "in", "fact": "degree_country", "values": values}
    rule = Rule.model_validate({"id": "r", "label": "l", "check": check, "citations": [CITE]})
    return evaluate(rule.check, Profile(degree_country=country), groups())


def test_in_with_group_references():
    saarland = ["@EHEA", "Switzerland", "UK"]
    assert exempt(saarland, "Germany").verdict == "meets"
    assert exempt(saarland, "Switzerland").verdict == "meets"
    assert exempt(saarland, "India").verdict == "does_not_meet"
    r = exempt(saarland, "Russia")                      # suspended EHEA member
    assert (r.verdict, r.reason) == ("unknown", "group_membership_uncertain")
    assert exempt(["@EHEA", "@LISBON"], "Russia").verdict == "meets"   # a second group settles it
    assert exempt(["@EU"], "Germany").verdict == "meets"
    assert exempt(["@EU"], "Norway").verdict == "does_not_meet"        # EEA is not built
    assert evaluate(Rule.model_validate({"id": "r", "label": "l", "citations": [CITE], "check":
        {"type": "in", "fact": "degree_country", "values": ["@EU"]}}).check, Profile(), groups()).verdict == "unknown"


def test_negated_group_keeps_uncertainty():
    check = {"type": "in", "fact": "degree_country", "values": ["@EHEA"], "negate": True}
    rule = Rule.model_validate({"id": "r", "label": "l", "check": check, "citations": [CITE]})
    run = lambda c: evaluate(rule.check, Profile(degree_country=c), groups()).verdict  # noqa: E731
    assert (run("India"), run("Germany"), run("Russia")) == ("meets", "does_not_meet", "unknown")


def test_old_country_lists_produce_a_notice():
    from eligibility.rules import load_ruleset

    rules, _ = load_ruleset(get_settings(), "kit-m-sc-computer-science")
    p = Profile(degree_country="India")
    assert check_eligibility(p, rules, as_of=date(2027, 10, 29)).notices == []     # on the last valid day
    late = check_eligibility(p, rules, as_of=date(2027, 10, 30)).notices
    assert len(late) == 2 and "re-check" in late[0]                                # EHEA and Lisbon
    no_groups = RuleSet(slug="s", record_sha256="x", rules=[
        {"id": "a", "label": "a", "check": {"type": "min", "fact": "total_credits", "value": "1"},
         "citations": [CITE]}])
    assert check_eligibility(p, no_groups, as_of=date(2030, 1, 1)).notices == []


def test_loader_rejects_unknown_fields(tmp_path):
    bad = tmp_path / "g.json"
    bad.write_text('{"schema_version":"x","groups":{},"surprise":1}')
    with pytest.raises(Exception):
        load_groups(str(bad))
