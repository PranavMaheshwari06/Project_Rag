"""What a check returns. Verdicts are per criterion; the headline is derived
from them and never means "admitted".

Admission, readiness (documents, deadlines) and finance get separate summaries
with their own headline words, so a missing document or a funds shortfall can
never read as an academic failure. `headline` is the admission headline."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from eligibility.rules import Category, Citation, Severity, Verdict

REPORT_SCHEMA_VERSION = "report-v1"

Headline = Literal[
    "meets_checked_published_requirements",
    "does_not_meet_published_requirements",
    "needs_information_or_review",
    "not_covered",
]
ReadinessHeadline = Literal[
    "ready_on_checked_items", "items_still_needed", "needs_information_or_review", "no_checked_items"
]
FinanceHeadline = Literal[
    "funds_cover_checked_reference", "funds_shortfall", "needs_information_or_review", "no_checked_items"
]


class Criterion(BaseModel):
    rule_id: str
    label: str
    category: Category = "admission"
    severity: Severity
    verdict: Verdict
    entered: str | None = None  # the student's value, as text
    required: str | None = None
    margin: Decimal | None = None  # positive = favourable
    reason: str | None = None  # reason code when verdict is unknown
    action: str | None = None  # deterministic template, never LLM text
    citations: list[Citation] = []


class Summary(BaseModel):
    """`counts` covers the area's hard and soft criteria that apply; inactive
    (not_applicable) and informational rules are not counted."""

    headline: Headline | ReadinessHeadline | FinanceHeadline
    counts: dict[str, int]


class Report(BaseModel):
    schema_version: str = REPORT_SCHEMA_VERSION
    slug: str
    headline: Headline
    admission: Summary
    readiness: Summary
    finance: Summary
    criteria: list[Criterion] = []
    rules_stale: bool = False
    notices: list[str] = []  # e.g. a country list past its re-check date
    rules_schema_version: str
    ruleset_sha256: str  # canonical hash of the rule file used
    record_sha256: str  # verified record the rules are bound to
    as_of: date | None = None
    tier: Literal["human", "second_pass"] | None = None  # verification tier of the record
