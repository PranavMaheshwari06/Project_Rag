"""What a check returns. Verdicts are per criterion; the headline is derived
from them and never means "admitted"."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from eligibility.rules import Citation, Severity, Verdict

Headline = Literal[
    "meets_checked_published_requirements",
    "does_not_meet_published_requirements",
    "needs_information_or_review",
    "not_covered",
]


class Criterion(BaseModel):
    rule_id: str
    label: str
    severity: Severity
    verdict: Verdict
    entered: str | None = None  # the student's value, as text
    required: str | None = None
    margin: Decimal | None = None  # positive = favourable
    reason: str | None = None  # reason code when verdict is unknown
    action: str | None = None  # deterministic template, never LLM text
    citations: list[Citation] = []


class Report(BaseModel):
    slug: str
    headline: Headline
    criteria: list[Criterion] = []
    rules_stale: bool = False
    notices: list[str] = []  # e.g. a country list past its re-check date
