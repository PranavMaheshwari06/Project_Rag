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
    taken_on: date | None = None


class EntranceTestResult(Strict):
    test: str  # "GRE" or "GATE"
    percentile: Decimal | None = None  # GRE: a percentile, never a raw score
    year: int | None = None
    qualified: bool | None = None  # GATE: reported qualifying result


class Profile(Strict):
    schema_version: str = SCHEMA_VERSION
    citizenships: list[str] | None = None
    degree_country: str | None = None
    school_country: str | None = None
    degree_title: str | None = None
    degree_completed: bool | None = None
    total_credits: Decimal | None = None
    credit_unit: str | None = None  # "ECTS" or another unit; other units are not converted
    subject_credits: dict[str, Decimal] | None = None  # student-confirmed allocation per area
    grade: Grade | None = None
    language: list[LanguageEvidence] | None = None
    entrance_tests: list[EntranceTestResult] | None = None
    documents: list[str] | None = None  # documents the student already has
    funds_eur: Decimal | None = Field(default=None, ge=0)
