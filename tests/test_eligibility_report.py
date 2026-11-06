"""Separate admission, readiness and finance summaries, and the version and hash
context a report carries. The existing `headline` keeps its meaning."""

from datetime import date

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.report import REPORT_SCHEMA_VERSION
from eligibility.rules import RuleSet, load_ruleset, record_tier, ruleset_hash

CITE = {"doc_id": "de/x/y", "quote": "q"}
PASS = {"type": "min", "fact": "total_credits", "value": "120"}
FAIL = {"type": "min", "fact": "total_credits", "value": "121"}
UNK = {"type": "min", "fact": "funds_eur", "value": "1"}
REVIEW = {"type": "university_review", "note": "the board decides"}
INACTIVE = {"type": "when", "when": FAIL, "then": PASS}
P = Profile(total_credits="120")


def ruleset(*rules, reviewed="human"):
    return RuleSet(
        slug="s",
        record_sha256="abc",
        rules=[
            {"id": f"r{i}", "label": f"rule {i}", "check": c, "citations": [CITE], "reviewed_by": reviewed, **extra}
            for i, (c, extra) in enumerate(rules)
        ],
    )


READY = {"category": "readiness"}
MONEY = {"category": "finance"}


def test_admission_summary_matches_the_headline():
    for rules in [((PASS, {}),), ((PASS, {}), (FAIL, {})), ((PASS, {}), (UNK, {})), ()]:
        rep = check_eligibility(P, ruleset(*rules))
        assert rep.admission.headline == rep.headline


def test_missed_readiness_item_is_not_an_academic_failure():
    rep = check_eligibility(P, ruleset((PASS, {}), (FAIL, READY)))
    assert rep.headline == "meets_checked_published_requirements"
    assert rep.admission.headline == "meets_checked_published_requirements"
    assert rep.readiness.headline == "items_still_needed"
    assert rep.criteria[1].action.startswith("Still needed")


def test_funds_shortfall_is_not_an_academic_failure():
    rep = check_eligibility(P, ruleset((PASS, {}), (FAIL, MONEY)))
    assert rep.headline == "meets_checked_published_requirements"
    assert rep.finance.headline == "funds_shortfall"
    assert "Not met" not in rep.criteria[1].action
    assert "academic" not in rep.criteria[1].action.casefold()


def test_area_headlines_pass_unknown_and_nothing_checked():
    rep = check_eligibility(P, ruleset((PASS, {}), (PASS, READY), (UNK, MONEY)))
    assert rep.readiness.headline == "ready_on_checked_items"
    assert rep.finance.headline == "needs_information_or_review"
    empty = check_eligibility(P, ruleset((PASS, {})))
    assert empty.readiness.headline == "no_checked_items"
    assert empty.finance.headline == "no_checked_items"


def test_pending_rule_never_gives_a_positive_area_headline():
    rep = check_eligibility(P, ruleset((PASS, READY), (PASS, MONEY), reviewed="pending"))
    assert rep.readiness.headline == "needs_information_or_review"
    assert rep.finance.headline == "needs_information_or_review"


def test_soft_readiness_failure_does_not_move_the_readiness_headline():
    rep = check_eligibility(P, ruleset((PASS, READY), (FAIL, {**READY, "severity": "soft"})))
    assert rep.readiness.headline == "ready_on_checked_items"
    assert rep.readiness.counts["does_not_meet"] == 1


def test_counts_by_verdict_per_area_skip_inactive_and_info_rules():
    rep = check_eligibility(
        P,
        ruleset(
            (PASS, {}), (FAIL, {}), (UNK, {}), (REVIEW, {}),
            (INACTIVE, {}), (REVIEW, {"severity": "info"}),
            (PASS, READY), (UNK, MONEY),
        ),
    )
    assert rep.admission.counts == {"meets": 1, "does_not_meet": 1, "unknown": 2, "not_published": 0}
    assert rep.readiness.counts == {"meets": 1, "does_not_meet": 0, "unknown": 0, "not_published": 0}
    assert rep.finance.counts == {"meets": 0, "does_not_meet": 0, "unknown": 1, "not_published": 0}
    assert [c.category for c in rep.criteria][-2:] == ["readiness", "finance"]


def test_stale_rules_give_review_in_the_programme_areas():
    rep = check_eligibility(P, ruleset((PASS, {}), (PASS, READY)), stale=True)
    for area in (rep.admission, rep.readiness):
        assert area.headline == "needs_information_or_review"
        assert sum(area.counts.values()) == 0
    # visa funds rules do not come from the programme record (see test_eligibility_finance)
    assert rep.finance.headline == "no_checked_items"


def test_report_carries_versions_hashes_date_and_tier():
    rs = ruleset((PASS, {}))
    rep = check_eligibility(P, rs, as_of=date(2027, 5, 1), tier="second_pass")
    assert rep.schema_version == REPORT_SCHEMA_VERSION
    assert rep.rules_schema_version == rs.schema_version
    assert rep.record_sha256 == "abc"
    assert rep.ruleset_sha256 == ruleset_hash(rs) and len(rep.ruleset_sha256) == 64
    assert rep.as_of == date(2027, 5, 1) and rep.tier == "second_pass"
    stale = check_eligibility(P, rs, stale=True, as_of=date(2027, 5, 1), tier="human")
    assert stale.ruleset_sha256 == rep.ruleset_sha256 and stale.tier == "human"


def test_ruleset_hash_ignores_formatting_but_not_content():
    a = ruleset((PASS, {}))
    b = RuleSet.model_validate_json(a.model_dump_json(indent=4))
    assert ruleset_hash(a) == ruleset_hash(b)
    assert ruleset_hash(a) != ruleset_hash(ruleset((FAIL, {})))


def test_real_files_report_their_record_tier():
    settings = load_settings()
    rules, stale = load_ruleset(settings, "kit-m-sc-computer-science")
    tier = record_tier(settings, "kit-m-sc-computer-science")
    assert tier in ("human", "second_pass")
    rep = check_eligibility(Profile(), rules, stale, tier=tier)
    assert rep.tier == tier and rep.record_sha256 == rules.record_sha256


def test_soft_or_info_only_area_reads_no_checked_items_but_counts_soft():
    rep = check_eligibility(
        P, ruleset((PASS, {}), (FAIL, {**READY, "severity": "soft"}), (REVIEW, {**MONEY, "severity": "info"}))
    )
    assert rep.readiness.headline == "no_checked_items"
    assert rep.readiness.counts["does_not_meet"] == 1
    assert rep.finance.headline == "no_checked_items"
    assert sum(rep.finance.counts.values()) == 0


def test_all_rules_inactive_gives_nothing_to_count():
    rep = check_eligibility(P, ruleset((INACTIVE, {}), (INACTIVE, READY)))
    assert rep.headline == "needs_information_or_review"
    assert rep.readiness.headline == "no_checked_items"
    assert sum(rep.admission.counts.values()) == 0


def test_area_headline_words_are_typed_per_area():
    import pytest
    from pydantic import ValidationError

    from eligibility.report import ReadinessSummary

    with pytest.raises(ValidationError):
        ReadinessSummary(headline="funds_shortfall", counts={})


def test_report_cannot_contradict_its_admission_summary():
    import pytest
    from pydantic import ValidationError

    from eligibility.report import Report

    data = check_eligibility(P, ruleset((FAIL, {}))).model_dump(mode="json")
    assert Report.model_validate(data).headline == "does_not_meet_published_requirements"
    data["headline"] = "meets_checked_published_requirements"
    with pytest.raises(ValidationError):
        Report.model_validate(data)
    data = check_eligibility(P, ruleset((PASS, {}))).model_dump(mode="json")
    data["readiness"]["counts"] = {"bogus": 1}
    with pytest.raises(ValidationError):
        Report.model_validate(data)


def test_every_real_rule_file_gives_a_consistent_report_for_an_empty_profile():
    settings = load_settings()
    from pathlib import Path

    for path in sorted(Path(settings.paths.rules_dir).glob("*.json")):
        rules, stale = load_ruleset(settings, path.stem)
        rep = check_eligibility(Profile(), rules, stale, tier=record_tier(settings, path.stem))
        assert rep.headline == rep.admission.headline == "needs_information_or_review", path.stem
        assert not any(c.verdict == "does_not_meet" for c in rep.criteria), path.stem
        counted = [c for c in rep.criteria if c.verdict != "not_applicable" and c.severity != "info"]
        total = sum(sum(s.counts.values()) for s in (rep.admission, rep.readiness, rep.finance))
        assert total == len(counted), path.stem
