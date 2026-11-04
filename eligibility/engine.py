"""Deterministic comparison of a Profile with a RuleSet. No LLM, no retrieval,
no clock: dates are compared with the request's `as_of`. A fact that was not
supplied is `unknown`, never a failure.

Margin: positive is favourable (observed - minimum, or maximum - observed). A
strict bound keeps its strictness at a zero margin."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from core.config import get_settings
from eligibility.finance import FinanceRules, finance_hash
from eligibility.groups import CountryGroups, load_groups
from eligibility.profile import Gate, Gre, Profile
from eligibility.report import AdmissionSummary, Criterion, FinanceSummary, ReadinessSummary, Report
from eligibility.rules import (
    BlockedAccount,
    Category,
    Check,
    Deadline,
    Group,
    In,
    Maximum,
    MaxAge,
    Minimum,
    Rule,
    RuleSet,
    Verdict,
    When,
    ruleset_hash,
)
from pydantic import BaseModel


class Result(BaseModel):
    verdict: Verdict
    entered: str | None = None
    required: str | None = None
    margin: Decimal | None = None
    reason: str | None = None  # why the verdict is unknown; "window_closed" for a missed deadline


@dataclass(frozen=True)
class Target:
    """What the check request owns, not the profile (plan section 3)."""

    as_of: date | None = None
    intake: Literal["winter", "summer"] | None = None
    starting_year: int | None = None


def shift_years(d: date, years: int) -> date:
    """Same day `years` later; 29 February becomes 28 February in a common year."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _deadline(check: Deadline, target: Target) -> Result:
    if target.intake is None:
        return Result(verdict="unknown", reason="missing_request_date")
    if target.intake != check.intake:
        return Result(verdict="not_applicable", entered=f"{target.intake} intake")
    if target.as_of is None or target.starting_year is None:
        return Result(verdict="unknown", reason="missing_request_date")
    if check.starting_years is not None and target.starting_year not in check.starting_years:
        return Result(verdict="unknown", reason="deadline_not_published_for_year")
    close = check.close.on(target.starting_year)
    entered = f"as of {target.as_of}"
    if check.open and target.as_of < check.open.on(target.starting_year):
        entered += f"; the window opens {check.open.on(target.starting_year)}"
    margin = Decimal((close - target.as_of).days)  # days left; negative = days late
    ok = margin >= 0  # the closing day itself is still in time
    return Result(verdict="meets" if ok else "does_not_meet", entered=entered, required=f"apply by {close}",
                  margin=margin, reason=None if ok else "window_closed")


def _max_age(check: MaxAge, profile: Profile, target: Target) -> Result:
    """With only a year known, decide only when every day of that year agrees."""
    required = f"not older than {check.years} years"
    observed = resolve(profile, check.fact)
    if observed is None:
        return Result(verdict="unknown", required=required, reason="missing_fact")
    if observed is ABSENT:
        return Result(verdict="does_not_meet", entered="not reported", required=required)
    if target.as_of is None:
        return Result(verdict="unknown", required=required, reason="missing_request_date")
    if isinstance(observed, date):
        earliest = latest = observed
    elif isinstance(observed, int) and not isinstance(observed, bool):
        earliest, latest = date(observed, 1, 1), date(observed, 12, 31)
    else:
        raise ValueError(f"fact {check.fact} is not a date or a year")
    if earliest > target.as_of:  # a result dated after the request date: a typo or a test not yet taken
        return Result(verdict="unknown", entered=str(observed), required=required, reason="date_after_as_of")
    if shift_years(earliest, check.years) >= target.as_of:
        verdict, margin = "meets", shift_years(earliest, check.years) - target.as_of
    elif shift_years(latest, check.years) < target.as_of:
        verdict, margin = "does_not_meet", shift_years(latest, check.years) - target.as_of
    else:
        return Result(verdict="unknown", entered=str(observed), required=required, reason="date_imprecise")
    return Result(verdict=verdict, entered=str(observed), required=required, margin=Decimal(margin.days))


ABSENT = object()  # the student listed their tests and this one is not among them, or said "none"
NO_TEST_FIELDS = {"gre": Gre, "gate": Gate}  # profile fields that accept "none"


def resolve(profile: Profile, path: str) -> object:
    """Dotted lookup; a missing link (None, absent dict key) gives None. In a list
    of language results a path part selects the entry by test name, e.g.
    `language.IELTS.overall`; a test missing from a supplied list is ABSENT, and
    so is any score of a test the student reported as "none"."""
    head, _, rest = path.partition(".")
    if head in NO_TEST_FIELDS and getattr(profile, head) == "none":
        if rest not in NO_TEST_FIELDS[head].model_fields:  # a typo must still fail loudly
            raise ValueError(f"unknown profile fact: {path}")
        return ABSENT
    cur: object = profile
    for part in path.split("."):
        if cur is None or cur is ABSENT:
            return cur
        if isinstance(cur, list):
            cur = next((e for e in cur if e.test.casefold() == part.casefold()), ABSENT)
        elif isinstance(cur, dict):
            cur = cur.get(part)
        elif hasattr(cur, part):
            cur = getattr(cur, part)
        else:
            raise ValueError(f"unknown profile fact: {path}")
    return cur


def _bound(check: Minimum | Maximum, profile: Profile) -> Result:
    smallest = isinstance(check, Minimum)
    required = f"{'>' if smallest else '<'}{'' if check.strict else '='} {check.value}"
    observed = resolve(profile, check.fact)
    if observed is None:
        return Result(verdict="unknown", required=required, reason="missing_fact")
    if observed is ABSENT:
        return Result(verdict="does_not_meet", entered="not reported", required=required)
    if not isinstance(observed, Decimal):
        raise ValueError(f"fact {check.fact} is not numeric")
    margin = observed - check.value if smallest else check.value - observed
    ok = margin > 0 if check.strict else margin >= 0
    return Result(
        verdict="meets" if ok else "does_not_meet",
        entered=str(observed),
        required=required,
        margin=margin,
    )


def _norm(v: object) -> object:
    """Numbers compare by value ("4" equals 4.0), other strings case-insensitively."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, Decimal)):
        return Decimal(v)
    if isinstance(v, str):
        try:
            return Decimal(v)
        except InvalidOperation:
            return v.casefold()
    return v


def default_groups() -> CountryGroups:
    return load_groups(get_settings().paths.country_groups_path)


def _in(check: In, profile: Profile, groups: CountryGroups | None) -> Result:
    required = f"{'not ' if check.negate else ''}one of {', '.join(map(str, check.values))}"
    observed = resolve(profile, check.fact)
    if observed is None:
        return Result(verdict="unknown", required=required, reason="missing_fact")
    if observed is ABSENT:  # no such test: it is in no list, so a negated check is met
        return Result(verdict="meets" if check.negate else "does_not_meet", entered="not reported", required=required)
    items = observed if isinstance(observed, list) else [observed]
    literals = {_norm(v) for v in check.values if not (isinstance(v, str) and v.startswith("@"))}
    refs = [v[1:] for v in check.values if isinstance(v, str) and v.startswith("@")]
    states = []  # a literal or any group match wins; an uncertain member only blocks a "no"
    for x in items:
        if _norm(x) in literals:
            states.append("member")
        for ref in refs:
            states.append((groups or default_groups()).membership(ref, str(x)))
    if "member" in states:
        hit = True
    elif "uncertain" in states:
        return Result(verdict="unknown", entered=str(observed), required=required, reason="group_membership_uncertain")
    else:
        hit = False
    return Result(verdict="meets" if hit != check.negate else "does_not_meet", entered=str(observed), required=required)


def _blocked_account(check: BlockedAccount, profile: Profile) -> Result:
    required = f">= {check.min_eur} EUR in a blocked account"
    if profile.funds is None:
        return Result(verdict="unknown", required=required, reason="missing_fact")
    if not profile.funds:
        return Result(verdict="does_not_meet", entered="not reported", required=required)
    if len(profile.funds) > 1 or profile.funds[0].route != "blocked_account":
        routes = ", ".join(f.route for f in profile.funds)
        return Result(verdict="unknown", entered=routes, required=required, reason="funds_route_not_comparable")
    amount = profile.funds[0].amount_eur
    margin = amount - check.min_eur
    return Result(verdict="meets" if margin >= 0 else "does_not_meet", entered=f"{amount} EUR",
                  required=required, margin=margin)


def evaluate(
    check: Check, profile: Profile, groups: CountryGroups | None = None, target: Target | None = None
) -> Result:
    target = target or Target()
    if isinstance(check, BlockedAccount):
        return _blocked_account(check, profile)
    if isinstance(check, Deadline):
        return _deadline(check, target)
    if isinstance(check, MaxAge):
        return _max_age(check, profile, target)
    if isinstance(check, (Minimum, Maximum)):
        return _bound(check, profile)
    if isinstance(check, In):
        return _in(check, profile, groups)
    if isinstance(check, When):
        cond = evaluate(check.when, profile, groups, target)
        if cond.verdict == "meets":
            return evaluate(check.then, profile, groups, target)
        if cond.verdict == "does_not_meet":
            return Result(verdict="not_applicable", entered=cond.entered)
        # an unresolved condition cannot make a requirement apply that is off anyway (e.g. the other intake)
        if evaluate(check.then, profile, groups, target).verdict == "not_applicable":
            return Result(verdict="not_applicable")
        return Result(verdict="unknown", reason=cond.reason or "condition_unresolved", required=cond.required)
    if isinstance(check, Group):
        results = [r for r in (evaluate(c, profile, groups, target) for c in check.children)
                   if r.verdict != "not_applicable"]
        if not results:
            return Result(verdict="not_applicable")
        verdicts = {r.verdict for r in results}
        # all_of: one known failure fails it. any_of: one pass passes it.
        decisive, other = (
            ("does_not_meet", "meets")
            if check.type == "all_of"
            else ("meets", "does_not_meet")
        )
        # keep "not reported" visible when every failing child is a test the student does not have
        failing = {r.entered for r in results if r.verdict == "does_not_meet"}
        entered = "not reported" if failing == {"not reported"} else None
        if decisive in verdicts:
            deciding = [r for r in results if r.verdict == decisive]
            if len(deciding) == 1:  # one child decides: keep its value, margin and reason
                return deciding[0]
            return Result(verdict=decisive, entered=entered if decisive == "does_not_meet" else None)
        if verdicts == {other}:
            if len(results) == 1:
                return results[0]
            return Result(verdict=other, entered=entered if other == "does_not_meet" else None)
        reason = next((r.reason for r in results if r.verdict == "unknown"), None)
        return Result(verdict="unknown", reason=reason)
    return Result(verdict="unknown", reason="university_review", required=check.note)


def check_funds(funds_eur: Decimal | None, required_eur: Decimal) -> Result:
    """Surplus (positive) or shortfall (negative) against a cited reference amount."""
    return _bound(
        Minimum(fact="funds_eur", value=required_eur), Profile(funds_eur=funds_eur)
    )


FAILED_ACTION = {"admission": "Not met", "readiness": "Still needed", "finance": "Funds below the reference"}

# area headline per resolved state: one known hard failure, all hard checks met
# and reviewed, something unresolved, or no applicable hard check at all
AREA_HEADLINES: dict[Category, dict[str, str]] = {
    "admission": {
        "fail": "does_not_meet_published_requirements",
        "pass": "meets_checked_published_requirements",
        "open": "needs_information_or_review",
        "none": "needs_information_or_review",
    },
    "readiness": {
        "fail": "items_still_needed",
        "pass": "ready_on_checked_items",
        "open": "needs_information_or_review",
        "none": "no_checked_items",
    },
    "finance": {
        "fail": "funds_shortfall",
        "pass": "funds_cover_checked_reference",
        "open": "needs_information_or_review",
        "none": "no_checked_items",
    },
}
COUNTED = ("meets", "does_not_meet", "unknown", "not_published")


def _action(rule: Rule, r: Result) -> str | None:
    if r.reason == "window_closed":
        return f"Application window closed: {rule.label}."
    if r.verdict == "does_not_meet" and rule.category == "finance" and r.entered == "not reported":
        return f"Proof of funds still needed: {rule.label}."
    if r.verdict == "does_not_meet":
        return f"{FAILED_ACTION[rule.category]}: {rule.label}."
    if r.reason == "missing_fact":
        return f"Provide the missing fact for: {rule.label}."
    if r.reason == "university_review":
        return f"The university decides: {r.required}"
    if r.reason == "funds_route_not_comparable":
        return f"The embassy decides whether this proof of funds is enough: {rule.label}."
    if r.reason == "group_membership_uncertain":
        return f"The university decides whether your degree country counts: {rule.label}."
    return None


def _group_refs(check: Check) -> set[str]:
    if isinstance(check, In):
        return {v[1:] for v in check.values if isinstance(v, str) and v.startswith("@")}
    if isinstance(check, When):
        return _group_refs(check.when) | _group_refs(check.then)
    if isinstance(check, Group):
        return set().union(*(_group_refs(c) for c in check.children))
    return set()


def _summary(category: Category, results: list[tuple[Rule, Result]], stale: bool) -> dict:
    """The admission summary's headline is the report headline (plan section 4)."""
    mine = [(rule, r) for rule, r in results if rule.category == category and r.verdict != "not_applicable"]
    counts = {v: sum(1 for rule, r in mine if r.verdict == v and rule.severity != "info") for v in COUNTED}
    hard = [(rule, r) for rule, r in mine if rule.severity == "hard"]
    if stale:
        state = "open"
    elif any(r.verdict == "does_not_meet" for _, r in hard):
        state = "fail"
    elif not hard:
        state = "none"
    elif all(r.verdict == "meets" and rule.reviewed_by != "pending" for rule, r in hard):
        state = "pass"
    else:  # unresolved fact, university judgment, or a rule nobody has reviewed yet
        state = "open"
    return {"headline": AREA_HEADLINES[category][state], "counts": counts}


def check_eligibility(
    profile: Profile,
    rules: RuleSet,
    stale: bool = False,
    as_of: date | None = None,
    groups: CountryGroups | None = None,
    tier: Literal["human", "second_pass"] | None = None,
    intake: Literal["winter", "summer"] | None = None,
    starting_year: int | None = None,
    finance: FinanceRules | None = None,
) -> Report:
    """One criterion per top-level rule; alternatives live inside their group.
    `as_of`, `intake` and `starting_year` come from the request: they place
    deadlines and test ages, and flag country lists past their re-check date.
    `finance` holds the visa funds rules, which apply to every programme."""
    target = Target(as_of=as_of, intake=intake, starting_year=starting_year)
    finance_rules = finance.rules if finance else []
    all_rules = rules.rules + finance_rules
    ids = [r.id for r in all_rules]
    if len(ids) != len(set(ids)):
        raise ValueError(f"a finance rule id repeats a programme rule id in {rules.slug}")
    # visa funds do not depend on the programme record, so stale programme rules do not hide them
    results = [(rule, evaluate(rule.check, profile, groups, target))
               for rule in ([] if stale else rules.rules) + finance_rules]
    criteria = [
        Criterion(
            rule_id=rule.id,
            label=rule.label,
            category=rule.category,
            severity=rule.severity,
            verdict=r.verdict,
            entered=r.entered,
            required=r.required,
            margin=r.margin,
            reason=r.reason,
            action=_action(rule, r),
            citations=rule.citations,
        )
        for rule, r in results
    ]
    admission = AdmissionSummary(**_summary("admission", results, stale))
    readiness = ReadinessSummary(**_summary("readiness", results, stale))
    funds = FinanceSummary(**_summary("finance", results, False))
    notices = []
    used = set().union(*(_group_refs(r.check) for r in all_rules))
    funds_apply = any(rule.category == "finance" and r.verdict != "not_applicable" for rule, r in results)
    if as_of and finance and funds_apply and as_of > finance.recheck_after:
        notices.append(f"The financial rules were read on {finance.fetched_on}; re-check the amounts on the cited pages.")
    if as_of and used and not stale:
        for name in sorted(used):
            g = (groups or default_groups()).groups[name]
            if as_of > g.recheck_after:
                notices.append(f"The {g.label} country list was last checked on {g.fetched_on}; re-check it ({g.source_url}).")
    return Report(
        slug=rules.slug,
        headline=admission.headline,
        admission=admission,
        readiness=readiness,
        finance=funds,
        criteria=criteria,
        rules_stale=stale,
        notices=notices,
        rules_schema_version=rules.schema_version,
        profile_schema_version=profile.schema_version,
        ruleset_sha256=ruleset_hash(rules),
        record_sha256=rules.record_sha256,
        finance_sha256=finance_hash(finance) if finance else None,
        as_of=as_of,
        intake=intake,
        starting_year=starting_year,
        tier=tier,
    )
