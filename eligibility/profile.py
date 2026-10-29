"""A student's confirmed facts. `None` means not supplied; `[]` or `0` means the
student said none. The engine never turns a missing value into a zero or a
False, so an incomplete profile is valid and yields `unknown`, not a failure.

Country of citizenship, of the qualifying degree and of schooling are separate
fields: rules key on one of them and must never substitute another."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "profile-v1"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Grade(Strict):
    """Original grade with its scale. Never assume a national passing mark."""

    obtained: Decimal
    best: Decimal
    passing: Decimal
    class_rank_percentile: Decimal | None = None  # 10 = top 10% of the class


class LanguageEvidence(Strict):
    test: str  # canonical name, e.g. "IELTS", "TOEFL iBT"; CEFR is a framework, not a test
    overall: Decimal | None = None
    components: dict[str, Decimal] | None = None
    grade: str | None = None  # letter grade, e.g. Cambridge CAE/CPE "A"
    taken_on: date | None = None


class Gre(Strict):
    """GRE General. Scaled scores and percentiles are different facts: a rule
    asking for a percentile never reads a scaled score, and vice versa."""

    quant: Decimal | None = None
    verbal: Decimal | None = None
    writing: Decimal | None = None
    quant_percentile: Decimal | None = None
    verbal_percentile: Decimal | None = None
    writing_percentile: Decimal | None = None
    taken_on: date | None = None


class Gate(Strict):
    paper: str | None = None  # GATE paper code, e.g. "CS", "DA"
    year: int | None = None
    qualified: bool | None = None  # as reported on the scorecard; no cutoff is invented


class Profile(Strict):
    schema_version: str = SCHEMA_VERSION
    # countries as English short names, as the university pages publish them ("India")
    citizenships: list[str] | None = None
    degree_country: str | None = None
    school_country: str | None = None
    degree_title: str | None = None
    degree_completed: bool | None = None
    total_credits: Decimal | None = None
    credit_unit: str | None = None  # "ECTS" or another unit; other units are not converted
    # student-confirmed credits per area, keyed in snake_case as the rules name them
    # (theoretical_cs, practical_cs, computer_engineering, mathematics, ...)
    subject_credits: dict[str, Decimal] | None = None
    grade: Grade | None = None
    language: list[LanguageEvidence] | None = None  # [] = student has no test
    english_instruction_share: Decimal | None = Field(default=None, ge=0, le=100)  # % of prior programme taught in English
    interview_passed: bool | None = None  # the target's aptitude interview, once taken (invited != passed)
    gre: Gre | None = None
    gate: Gate | None = None
    documents: list[str] | None = None  # document keys the student already has, e.g. "aps_certificate"
    funds_eur: Decimal | None = Field(default=None, ge=0)
