"""The reviewed rule catalogue: typed rules derived from a verified record.

A record says what the page says; a rule says how the engine compares a student
with it. Each rule carries its own citations and review status, and the whole
file is bound to the SHA-256 of the verified record it was derived from. If the
record changes, the catalogue is `stale` and the engine must not use it.

Checks are a small closed set (no expression language): numeric bounds,
all_of / any_of groups and an explicit university-review step."""

import hashlib
import json
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


class Group(Strict):
    type: Literal["all_of", "any_of"]
    children: list["Check"]

    @model_validator(mode="after")
    def _not_empty(self):
        if not self.children:
            raise ValueError("a group needs at least one child")
        return self


Check = Annotated[Minimum | Maximum | In | When | UniversityReview | Group, Field(discriminator="type")]
Group.model_rebuild()
When.model_rebuild()


class Rule(Strict):
    id: str
    label: str
    category: Category = "admission"
    severity: Severity = "hard"
    check: Check
    citations: list[Citation] = Field(min_length=1)
    reviewed_by: Literal["pending", "model", "human"] = "pending"


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


def uncited_quotes(rules: RuleSet, record: dict) -> list[str]:
    """Rule citations whose quote is not inside a quote of the verified record
    from the same doc (word-normalised, as the extraction quote check)."""
    from extraction.extract import _words

    cited: dict[str, list[str]] = {}
    for field in record.values():
        if isinstance(field, dict) and field.get("quote"):
            cited.setdefault(field["doc_id"], []).append(_words(field["quote"]))
            for s in field.get("supporting_citations", []):
                cited.setdefault(s["doc_id"], []).append(_words(s["quote"]))
    return [f"{r.id}: {c.quote[:60]!r}" for r in rules.rules for c in r.citations
            if not any(_words(c.quote) in q for q in cited.get(c.doc_id, []))]


def load_ruleset(settings: Settings, slug: str) -> tuple[RuleSet, bool]:
    """Return the rules and whether they are stale against the verified record."""
    rules = RuleSet.model_validate_json(
        (Path(settings.paths.rules_dir) / f"{slug}.json").read_text(encoding="utf-8"))
    wrapper = json.loads((Path(settings.paths.verified_dir) / f"{slug}.json").read_text(encoding="utf-8"))
    return rules, rules.record_sha256 != record_hash(wrapper["record"])
