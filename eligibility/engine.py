"""Deterministic comparison of a Profile with a RuleSet. No LLM, no retrieval,
no clock. A fact that was not supplied is `unknown`, never a failure.

Margin: positive is favourable (observed - minimum, or maximum - observed). A
strict bound keeps its strictness at a zero margin."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from core.config import get_settings
from eligibility.groups import CountryGroups, load_groups
from eligibility.profile import Profile
from eligibility.report import AdmissionSummary, Criterion, FinanceSummary, ReadinessSummary, Report
from eligibility.rules import (
    Category,
    Check,
    Group,
    In,
    Maximum,
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
    reason: str | None = None  # why the verdict is unknown


ABSENT = object()  # the student listed their tests and this one is not among them


def resolve(profile: Profile, path: str) -> object:
    """Dotted lookup; a missing link (None, absent dict key) gives None. In a list
    of language results a path part selects the entry by test name, e.g.
    `language.IELTS.overall`; a test missing from a supplied list is ABSENT, and
    so is any score of a test the student reported as "none"."""
    cur: object = profile
    for part in path.split("."):
        if cur is None or cur is ABSENT:
            return cur
        if cur == "none":
            return ABSENT
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
    if observed is ABSENT:
        return Result(verdict="does_not_meet", entered="not reported", required=required)
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


def evaluate(check: Check, profile: Profile, groups: CountryGroups | None = None) -> Result:
    if isinstance(check, (Minimum, Maximum)):
        return _bound(check, profile)
    if isinstance(check, In):
        return _in(check, profile, groups)
    if isinstance(check, When):
        cond = evaluate(check.when, profile, groups)
        if cond.verdict == "meets":
            return evaluate(check.then, profile, groups)
        if cond.verdict == "does_not_meet":
            return Result(verdict="not_applicable", entered=cond.entered)
        return Result(verdict="unknown", reason=cond.reason or "condition_unresolved", required=cond.required)
    if isinstance(check, Group):
        results = [r for r in (evaluate(c, profile, groups) for c in check.children) if r.verdict != "not_applicable"]
        if not results:
            return Result(verdict="not_applicable")
        verdicts = {r.verdict for r in results}
        # all_of: one known failure fails it. any_of: one pass passes it.
        decisive, other = (
            ("does_not_meet", "meets")
            if check.type == "all_of"
            else ("meets", "does_not_meet")
        )
        if decisive in verdicts:
            return Result(verdict=decisive)
        if verdicts == {other}:
            return Result(verdict=other)
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
    if r.verdict == "does_not_meet":
        return f"{FAILED_ACTION[rule.category]}: {rule.label}."
    if r.reason == "missing_fact":
        return f"Provide the missing fact for: {rule.label}."
    if r.reason == "university_review":
        return f"The university decides: {r.required}"
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
) -> Report:
    """One criterion per top-level rule; alternatives live inside their group.
    `as_of` is only used to flag country lists past their re-check date."""
    results = [] if stale else [(rule, evaluate(rule.check, profile, groups)) for rule in rules.rules]
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
    finance = FinanceSummary(**_summary("finance", results, stale))
    notices = []
    used = set().union(*(_group_refs(r.check) for r in rules.rules))
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
        finance=finance,
        criteria=criteria,
        rules_stale=stale,
        notices=notices,
        rules_schema_version=rules.schema_version,
        ruleset_sha256=ruleset_hash(rules),
        record_sha256=rules.record_sha256,
        as_of=as_of,
        tier=tier,
    )
