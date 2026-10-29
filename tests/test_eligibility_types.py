import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.config import get_settings
from eligibility.profile import Profile
from eligibility.rules import Group, Rule, RuleSet, load_ruleset, record_hash

CITE = {"doc_id": "de/x/y", "quote": "at least 120 ECTS"}


def rule(rid="r1", check=None):
    check = check or {"type": "min", "fact": "total_credits", "value": "120"}
    return {"id": rid, "label": "credits", "check": check, "citations": [CITE]}


def test_missing_is_not_zero():
    p = Profile()
    assert p.total_credits is None and p.documents is None
    assert Profile(documents=[]).documents == []  # explicitly none
    assert Profile(total_credits="0").total_credits == Decimal("0")


def test_profile_round_trip_and_rejects_unknown_fields():
    p = Profile(total_credits="180", citizenships=["IN"])
    assert Profile.model_validate_json(p.model_dump_json()) == p
    with pytest.raises(ValidationError):
        Profile(gpa=3.5)
    with pytest.raises(ValidationError):
        Profile(funds_eur=-1)


def test_money_stays_decimal():
    assert Profile(funds_eur="11904.1").funds_eur == Decimal("11904.1")


def test_empty_group_and_duplicate_ids_rejected():
    with pytest.raises(ValidationError):
        Group(type="any_of", children=[])
    with pytest.raises(ValidationError):
        RuleSet(slug="s", record_sha256="x", rules=[rule(), rule()])


def test_rule_needs_citation():
    bad = rule()
    bad["citations"] = []
    with pytest.raises(ValidationError):
        Rule.model_validate(bad)


def test_nested_group_parses():
    group = {"type": "any_of", "children": [
        {"type": "min", "fact": "total_credits", "value": "120"},
        {"type": "university_review", "note": "board decides"}]}
    assert Rule.model_validate(rule(check=group)).check.children[1].type == "university_review"


def test_ruleset_bound_to_record_hash(tmp_path):
    s = get_settings()
    s.paths.verified_dir, s.paths.rules_dir = str(tmp_path / "v"), str(tmp_path / "r")
    (tmp_path / "v").mkdir(), (tmp_path / "r").mkdir()
    record = {"university": "U", "programme": "P"}
    (tmp_path / "v" / "u-p.json").write_text(json.dumps({"tier": "human", "record": record}))
    rs = RuleSet(slug="u-p", record_sha256=record_hash(record), rules=[rule()])
    (tmp_path / "r" / "u-p.json").write_text(rs.model_dump_json())
    assert load_ruleset(s, "u-p")[1] is False
    record["programme"] = "changed"
    (tmp_path / "v" / "u-p.json").write_text(json.dumps({"tier": "human", "record": record}))
    assert load_ruleset(s, "u-p")[1] is True  # stale: engine must refuse


def test_hash_matches_inventory_script():
    from pathlib import Path
    inv = json.loads(Path("data/eligibility/coverage_inventory.json").read_text())
    slug, prog = next(iter(inv["programmes"].items()))
    wrapper = json.loads(Path(f"data/verified/{slug}.json").read_text())
    assert record_hash(wrapper["record"]) == prog["record_sha256"]
