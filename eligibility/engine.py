"""Deterministic comparison of a Profile with a RuleSet. No LLM, no retrieval,
no clock. A fact that was not supplied is `unknown`, never a failure.

Margin: positive is favourable (observed - minimum, or maximum - observed). A
strict bound keeps its strictness at a zero margin."""

from decimal import Decimal

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


def _in(check: In, profile: Profile) -> Result:
    required = f"{'not ' if check.negate else ''}one of {', '.join(map(str, check.values))}"
    observed = resolve(profile, check.fact)
    if observed is None:
        return Result(verdict="unknown", required=required, reason="missing_fact")
    if observed is ABSENT:
        return Result(verdict="does_not_meet", entered="not reported", required=required)
    allowed = {_norm(v) for v in check.values}
    items = observed if isinstance(observed, list) else [observed]
    hit = any(_norm(x) in allowed for x in items) != check.negate
    return Result(verdict="meets" if hit else "does_not_meet", entered=str(observed), required=required)


def evaluate(check: Check, profile: Profile) -> Result:
    if isinstance(check, (Minimum, Maximum)):
        return _bound(check, profile)
    if isinstance(check, In):
        return _in(check, profile)
    if isinstance(check, When):
        cond = evaluate(check.when, profile)
        if cond.verdict == "meets":
            return evaluate(check.then, profile)
        if cond.verdict == "does_not_meet":
            return Result(verdict="not_applicable", entered=cond.entered)
        return Result(verdict="unknown", reason=cond.reason or "condition_unresolved", required=cond.required)
    if isinstance(check, Group):
        results = [r for r in (evaluate(c, profile) for c in check.children) if r.verdict != "not_applicable"]
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
    return None


def check_eligibility(profile: Profile, rules: RuleSet, stale: bool = False) -> Report:
    """One criterion per top-level rule; alternatives live inside their group."""
    if stale:  # the record changed since the rules were reviewed: no verdicts
        return Report(
            slug=rules.slug, headline="needs_information_or_review", rules_stale=True
        )
    criteria, admission = [], []
    for rule in rules.rules:
        r = evaluate(rule.check, profile)
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
    return Report(slug=rules.slug, headline=headline, criteria=criteria)
