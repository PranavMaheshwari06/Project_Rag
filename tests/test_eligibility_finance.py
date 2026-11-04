"""Visa funds: a cited financial-rule file and funds entered per proof route.
A lone blocked account is compared with the published amount; any other route,
or a combination, is "unknown" because no rule for combining proofs is
published. A shortfall is a finance outcome, never an academic failure."""

from datetime import date, timedelta
from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from core.config import load_settings
from eligibility.engine import check_eligibility, evaluate
from eligibility.finance import FinanceRules, load_finance
from eligibility.profile import SCHEMA_VERSION, Profile
from eligibility.rules import Rule, RuleSet, load_ruleset

CITE = {"doc_id": "de/x/y", "quote": "q"}
LONE = {"type": "blocked_account", "min_eur": "11904"}
INDIA = {"citizenships": ["India"], "visa_country": "India"}


def ev(check, **facts):
    rule = Rule.model_validate({"id": "r", "label": "l", "category": "finance", "check": check, "citations": [CITE]})
    return evaluate(rule.check, Profile(**facts))


def blocked(amount):
    return [{"route": "blocked_account", "amount_eur": amount}]


# --- profile ------------------------------------------------------------------------
def test_profile_v3_round_trip_and_routes_are_a_closed_list():
    assert SCHEMA_VERSION == "profile-v3"
    p = Profile(funds=blocked("11904.00"), visa_country="India")
    assert Profile.model_validate_json(p.model_dump_json()) == p
    assert p.funds[0].amount_eur == D("11904.00")
    with pytest.raises(ValidationError):
        Profile(funds=[{"route": "savings", "amount_eur": "1"}])
    with pytest.raises(ValidationError):
        Profile(funds=[{"route": "blocked_account", "amount_eur": "-1"}])
    assert Profile.model_validate({"schema_version": "profile-v2", "gre": "none"}).gre == "none"


# --- the check ----------------------------------------------------------------------
def test_lone_blocked_account_at_the_boundary():
    at = ev(LONE, funds=blocked("11904"))
    assert at.verdict == "meets" and at.margin == 0
    short = ev(LONE, funds=blocked("11903.99"))
    assert short.verdict == "does_not_meet" and short.margin == D("-0.01")
    assert ev(LONE, funds=blocked("12000.50")).margin == D("96.50")


def test_missing_none_and_other_routes():
    assert ev(LONE).reason == "missing_fact"
    none = ev(LONE, funds=[])
    assert none.verdict == "does_not_meet" and none.entered == "not reported"
    for funds in (
        [{"route": "declaration_of_commitment", "amount_eur": "20000"}],
        [{"route": "scholarship", "amount_eur": "20000"}],
        blocked("12000") + [{"route": "education_loan", "amount_eur": "5000"}],
        blocked("6000") + blocked("6000"),
    ):
        r = ev(LONE, funds=funds)
        assert r.verdict == "unknown" and r.reason == "funds_route_not_comparable", funds


def test_old_funds_eur_total_is_not_a_proof_route():
    assert ev(LONE, funds_eur="20000").reason == "missing_fact"


# --- the cited file -----------------------------------------------------------------
def test_finance_file_is_cited_dated_and_pending():
    fin = load_finance(load_settings().paths.finance_rules_path)
    assert fin.fetched_on == date(2026, 11, 4) and fin.recheck_after > fin.fetched_on
    assert all(r.category == "finance" and r.reviewed_by == "pending" for r in fin.rules)
    assert any("11,904" in c.quote for r in fin.rules for c in r.citations)


def test_finance_file_rejects_non_finance_rules():
    with pytest.raises(ValidationError):
        FinanceRules.model_validate({
            "schema_version": "finance-v1", "fetched_on": "2026-11-04", "recheck_after": "2027-05-04",
            "rules": [{"id": "r", "label": "l", "category": "admission", "check": LONE, "citations": [CITE]}],
        })


def report(profile, as_of=date(2027, 3, 1)):
    s = load_settings()
    rules, stale = load_ruleset(s, "kit-m-sc-computer-science")
    return check_eligibility(profile, rules, stale, as_of=as_of, finance=load_finance(s.paths.finance_rules_path))


def test_india_mission_applicant_with_a_lone_blocked_account():
    rep = report(Profile(**INDIA, funds=blocked("11000")))
    crit = next(c for c in rep.criteria if c.category == "finance")
    assert crit.verdict == "does_not_meet" and crit.margin == D("-904")
    assert rep.finance.headline == "funds_shortfall"
    assert rep.headline != "does_not_meet_published_requirements" or any(
        c.verdict == "does_not_meet" for c in rep.criteria if c.category == "admission"
    )
    assert rep.finance_sha256 and len(rep.finance_sha256) == 64
    ok = report(Profile(**INDIA, funds=blocked("11904")))
    # pending rule: a met amount still reads as review, never as settled
    assert ok.finance.headline == "needs_information_or_review"


def test_finance_rule_scope():
    eu = report(Profile(citizenships=["Germany"], funds=blocked("1")))
    assert next(c for c in eu.criteria if c.category == "finance").verdict == "not_applicable"
    other_mission = report(Profile(citizenships=["India"], visa_country="Nepal", funds=blocked("1")))
    assert next(c for c in other_mission.criteria if c.category == "finance").verdict == "not_applicable"
    unknown = report(Profile(funds=blocked("1")))
    assert next(c for c in unknown.criteria if c.category == "finance").verdict == "unknown"


def test_finance_recheck_date_gives_a_notice():
    s = load_settings()
    fin = load_finance(s.paths.finance_rules_path)
    late = report(Profile(**INDIA), as_of=fin.recheck_after + timedelta(days=1))
    assert any("financial rules" in n for n in late.notices)
    assert not any("financial rules" in n for n in report(Profile(**INDIA), as_of=fin.recheck_after).notices)


def test_no_finance_rules_keeps_finance_unchecked():
    rs = RuleSet(slug="s", record_sha256="x", rules=[])
    rep = check_eligibility(Profile(**INDIA, funds=blocked("1")), rs)
    assert rep.finance.headline == "no_checked_items" and rep.finance_sha256 is None


def test_validate_reads_the_finance_file_and_cli_reports_finance(capsys, monkeypatch, tmp_path):
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("check_eligibility_cli_fin", root / "scripts" / "check_eligibility.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    settings = load_settings()
    settings.paths.raw_dir = str(tmp_path)  # no cache: finance quotes are reported, not silently passed
    assert cli.validate(settings) == []
    assert "finance: blocked_account_first_year: cached page unavailable, not checked" in capsys.readouterr().out
    profile = tmp_path / "p.json"
    profile.write_text(Profile(**INDIA, funds=blocked("12000")).model_dump_json())
    monkeypatch.setattr(sys, "argv", ["x", "--profile", str(profile), "--programme", "kit-m-sc-computer-science",
                                      "--as-of", "2027-03-01"])
    assert cli.main() == 0
    assert "finance: needs_information_or_review (1 meets)" in capsys.readouterr().out


def test_eval_results_hash_the_finance_file():
    from evaluation.eligibility_eval import run_cases

    out = run_cases([], load_settings())
    assert len(out["hashes"]["finance_sha256"]) == 64
