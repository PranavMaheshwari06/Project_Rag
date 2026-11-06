"""What a check returns. Verdicts are per criterion; the headline is derived
from them and never means "admitted".

Admission, readiness (documents, deadlines) and finance get separate summaries
with their own headline words, so a missing document or a funds shortfall can
never read as an academic failure. `headline` is the admission headline."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, NonNegativeInt, model_validator

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
    (not_applicable) and informational rules are not counted. Only hard rules
    set the headline, so an area with soft rules alone reads `no_checked_items`."""

    counts: dict[Literal["meets", "does_not_meet", "unknown", "not_published"], NonNegativeInt]


class AdmissionSummary(Summary):
    headline: Headline


class ReadinessSummary(Summary):
    headline: ReadinessHeadline


class FinanceSummary(Summary):
    headline: FinanceHeadline


class Report(BaseModel):
    schema_version: str = REPORT_SCHEMA_VERSION
    slug: str
    headline: Headline
    admission: AdmissionSummary
    readiness: ReadinessSummary
    finance: FinanceSummary
    criteria: list[Criterion] = []
    rules_stale: bool = False
    notices: list[str] = []  # e.g. a country list past its re-check date
    rules_schema_version: str
    profile_schema_version: str
    ruleset_sha256: str  # canonical hash of the rule set as loaded (defaults filled in)
    finance_sha256: str | None = None  # canonical hash of the financial rules used, if any
    record_sha256: str  # the verified record the rules are bound to; differs from disk when rules_stale
    as_of: date | None = None
    intake: Literal["winter", "summer"] | None = None
    starting_year: int | None = None
    tier: Literal["human", "second_pass"] | None = None  # verification tier of the record

    @model_validator(mode="after")
    def _headline_is_admission(self):
        if self.headline != self.admission.headline:
            raise ValueError("headline must equal the admission summary's headline")
        return self
