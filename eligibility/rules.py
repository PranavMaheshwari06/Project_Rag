"""The reviewed rule catalogue: typed rules derived from a verified record.

A record says what the page says; a rule says how the engine compares a student
with it. Each rule carries its own citations and review status, and the whole
file is bound to the SHA-256 of the verified record it was derived from. If the
record changes, the catalogue is `stale` and the engine must not use it.

Checks are a small closed set (no expression language): numeric bounds,
membership, conditions, all_of / any_of groups, an explicit university-review
step, two date checks (an application deadline and a maximum age) and the
blocked-account funds check."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.config import Settings

SCHEMA_VERSION = "rules-v1"

# not_applicable: a condition (e.g. degree country) switched the rule off; it is
# shown in the trace but never counted
Verdict = Literal["meets", "does_not_meet", "unknown", "not_published", "not_applicable"]
Severity = Literal["hard", "soft", "info"]
Category = Literal["admission", "readiness", "finance"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(Strict):
    doc_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class Minimum(Strict):
    type: Literal["min"] = "min"
    fact: str  # dotted path into the Profile, e.g. "total_credits"
    value: Decimal
    strict: bool = False  # True: observed must be greater than value, not equal


class Maximum(Strict):
    type: Literal["max"] = "max"
    fact: str
    value: Decimal
    strict: bool = False


class In(Strict):
    """Fact is one of `values` (strings compared case-insensitively). A list fact
    such as `documents` meets if any element matches. `negate` flips the result."""

    type: Literal["in"] = "in"
    fact: str
    values: list[str | bool] = Field(min_length=1)
    negate: bool = False


class When(Strict):
    """`then` applies only if `when` meets. If `when` fails the rule is
    not_applicable; if `when` is unknown the rule stays unknown, never exempt."""

    type: Literal["when"] = "when"
    when: "Check"
    then: "Check"


class UniversityReview(Strict):
    """A step only the university can resolve; never `meets` on its own."""

    type: Literal["university_review"] = "university_review"
    note: str


class DayOfYear(Strict):
    """A recurring date, placed relative to the intake's starting year (the
    calendar year the term starts: winter 2027/28 and summer 2027 both have
    2027). A summer 2027 intake with a deadline in November 2026 has -1."""

    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    year_offset: int = 0

    @model_validator(mode="after")
    def _real_day(self):
        date(2001, self.month, self.day)  # raises for 30 February; 29 February is refused too
        return self

    def on(self, starting_year: int) -> date:
        return date(starting_year + self.year_offset, self.month, self.day)


class Deadline(Strict):
    """Apply by `close` (inclusive) for this intake. `starting_years`: the page
    publishes dated windows only for these years; other years stay unknown."""

    type: Literal["deadline"] = "deadline"
    intake: Literal["winter", "summer"]
    close: DayOfYear
    open: DayOfYear | None = None
    starting_years: list[int] | None = None

    @model_validator(mode="after")
    def _opens_before_it_closes(self):
        if self.open and self.open.on(2001) > self.close.on(2001):
            raise ValueError("a window cannot open after it closes")
        return self


class MaxAge(Strict):
    """A test or certificate not older than `years` on the request's as_of date
    (pages that name another reference date need another check). The fact is a
    date, or a year when only the year is known."""

    type: Literal["max_age"] = "max_age"
    fact: str
    years: int = Field(ge=1)


class BlockedAccount(Strict):
    """Visa funds: a lone blocked account compared with `min_eur`. Any other
    route, or a combination, is unknown: no rule for combining proofs is published."""

    type: Literal["blocked_account"] = "blocked_account"
    min_eur: Decimal = Field(gt=0)


class NotPublished(Strict):
    """The source publishes no minimum here: shown in the trace, never met or
    failed, never counted. `record_field` names a verified-record field whose
    status must be not_published, so the claim is tied to the verified record."""

    type: Literal["not_published"] = "not_published"
    note: str
    record_field: str | None = None


class Group(Strict):
    type: Literal["all_of", "any_of"]
    children: list["Check"]

    @model_validator(mode="after")
    def _not_empty(self):
        if not self.children:
            raise ValueError("a group needs at least one child")
        return self


Check = Annotated[
    Minimum | Maximum | In | When | UniversityReview | Deadline | MaxAge | BlockedAccount | NotPublished | Group,
    Field(discriminator="type"),
]
Group.model_rebuild()
When.model_rebuild()


def _nests_not_published(check: "Check") -> bool:
    if isinstance(check, NotPublished):
        return True
    if isinstance(check, When):
        return _nests_not_published(check.when) or _nests_not_published(check.then)
    if isinstance(check, Group):
        return any(_nests_not_published(c) for c in check.children)
    return False


class Rule(Strict):
    id: str
    label: str
    category: Category = "admission"
    severity: Severity = "hard"
    check: Check
    citations: list[Citation] = Field(min_length=1)
    reviewed_by: Literal["pending", "model", "human"] = "pending"

    @model_validator(mode="after")
    def _not_published_is_info(self):
        if isinstance(self.check, NotPublished) and self.severity != "info":
            raise ValueError("a not_published rule is informational: severity must be info")
        if not isinstance(self.check, NotPublished) and _nests_not_published(self.check):
            raise ValueError("not_published is only allowed as a rule's whole check, never inside a group")
        return self


class RuleSet(Strict):
    schema_version: str = SCHEMA_VERSION
    slug: str
    record_sha256: str  # hash of the verified record these rules were derived from
    rules: list[Rule]

    @model_validator(mode="after")
    def _unique_ids(self):
        ids = [r.id for r in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate rule id")
        return self


def record_hash(record: dict) -> str:
    """Same canonical form as scripts/validate_phase6_inventory.py."""
    blob = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def ruleset_hash(rules: RuleSet) -> str:
    """Canonical hash of the rule set as loaded (defaults filled in): whitespace
    and key order do not count; a number written differently ("4" vs "4.0") or
    a changed code default does."""
    return record_hash(rules.model_dump(mode="json"))


def not_published_mismatches(rules: RuleSet, record: dict) -> list[str]:
    """Rule ids whose not_published claim is not backed by the record field."""
    def backed(field: str) -> bool:
        value = record.get(field)
        return isinstance(value, dict) and value.get("status") == "not_published"

    return [r.id for r in rules.rules if isinstance(r.check, NotPublished) and r.check.record_field
            and not backed(r.check.record_field)]


def uncited_quotes(rules: RuleSet, record: dict) -> list[tuple[str, str, str]]:
    """(rule id, doc id, quote) for citations not inside a quote of the verified
    record from the same doc (word-normalised, as the extraction quote check)."""
    from extraction.extract import _words

    cited: dict[str, list[str]] = {}
    for field in record.values():
        if isinstance(field, dict) and field.get("quote"):
            cited.setdefault(field["doc_id"], []).append(_words(field["quote"]))
            for s in field.get("supporting_citations", []):
                cited.setdefault(s["doc_id"], []).append(_words(s["quote"]))
    return [(r.id, c.doc_id, c.quote) for r in rules.rules for c in r.citations
            if not any(_words(c.quote) in q for q in cited.get(c.doc_id, []))]


def record_tier(settings: Settings, slug: str) -> Literal["human", "second_pass"]:
    wrapper = json.loads((Path(settings.paths.verified_dir) / f"{slug}.json").read_text(encoding="utf-8"))
    return wrapper["tier"]


def load_ruleset(settings: Settings, slug: str) -> tuple[RuleSet, bool]:
    """Return the rules and whether they are stale against the verified record."""
    rules = RuleSet.model_validate_json(
        (Path(settings.paths.rules_dir) / f"{slug}.json").read_text(encoding="utf-8"))
    wrapper = json.loads((Path(settings.paths.verified_dir) / f"{slug}.json").read_text(encoding="utf-8"))
    return rules, rules.record_sha256 != record_hash(wrapper["record"])
