"""Deterministic comparison of a Profile with a RuleSet. No LLM, no retrieval,
no clock. A fact that was not supplied is `unknown`, never a failure.

Margin: positive is favourable (observed - minimum, or maximum - observed). A
strict bound keeps its strictness at a zero margin."""

from datetime import date
from decimal import Decimal

from core.config import get_settings
from eligibility.groups import CountryGroups, load_groups
from eligibility.profile import Profile
from eligibility.report import Criterion, Headline, Report
from eligibility.rules import (
    Check,
    Group,
    In,
    Maximum,
    Minimum,
    Rule,
    RuleSet,
    Verdict,
    When,
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
    `language.IELTS.overall`; a test missing from a supplied list is ABSENT."""
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
    return v.casefold() if isinstance(v, str) else v


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


def _action(rule: Rule, r: Result) -> str | None:
    if r.verdict == "does_not_meet":
        return f"{'Still needed' if rule.category == 'readiness' else 'Not met'}: {rule.label}."
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


def check_eligibility(
    profile: Profile,
    rules: RuleSet,
    stale: bool = False,
    as_of: date | None = None,
    groups: CountryGroups | None = None,
) -> Report:
    """One criterion per top-level rule; alternatives live inside their group.
    `as_of` is only used to flag country lists past their re-check date."""
    if stale:  # the record changed since the rules were reviewed: no verdicts
        return Report(
            slug=rules.slug, headline="needs_information_or_review", rules_stale=True
        )
    criteria, admission = [], []
    for rule in rules.rules:
        r = evaluate(rule.check, profile, groups)
        criteria.append(
            Criterion(
                rule_id=rule.id,
                label=rule.label,
                severity=rule.severity,
                verdict=r.verdict,
                entered=r.entered,
                required=r.required,
                margin=r.margin,
                reason=r.reason,
                action=_action(rule, r),
                citations=rule.citations,
            )
        )
        if rule.category == "admission" and rule.severity == "hard" and r.verdict != "not_applicable":
            admission.append((rule, r))
    headline: Headline
    if any(r.verdict == "does_not_meet" for _, r in admission):
        headline = "does_not_meet_published_requirements"
    elif admission and all(
        r.verdict == "meets" and rule.reviewed_by != "pending" for rule, r in admission
    ):
        headline = "meets_checked_published_requirements"
    else:  # unresolved fact, university judgment, or a rule nobody has reviewed yet
        headline = "needs_information_or_review"
    notices = []
    used = set().union(*(_group_refs(r.check) for r in rules.rules))
    if as_of and used:
        for name in sorted(used):
            g = (groups or default_groups()).groups[name]
            if as_of > g.recheck_after:
                notices.append(f"The {g.label} country list was last checked on {g.fetched_on}; re-check it ({g.source_url}).")
    return Report(slug=rules.slug, headline=headline, criteria=criteria, notices=notices)
