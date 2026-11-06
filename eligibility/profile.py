"""A student's confirmed facts. `None` means not supplied; `[]` or `0` means the
student said none; for GRE and GATE, which are objects, the literal "none"
means the student has no such test. The engine never turns a missing value into a zero or a
False, so an incomplete profile is valid and yields `unknown`, not a failure.

Country of citizenship, of the qualifying degree and of schooling are separate
fields: rules key on one of them and must never substitute another."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "profile-v5"  # v2: gre/gate accept "none"; v3: funds per proof route, visa_country;
# v4: credit_unit is a closed choice; v5: university_assessments
# an older profile is a valid newer one, except a free-text credit_unit from v1-v3,
# which must be re-entered as "ECTS" (LP, CP, ECTS credits) or "other"
ProfileVersion = Literal["profile-v1", "profile-v2", "profile-v3", "profile-v4", "profile-v5"]
NoTest = Literal["none"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Grade(Strict):
    """Original grade with its scale. Never assume a national passing mark."""

    obtained: Decimal
    best: Decimal
    passing: Decimal
    class_rank_percentile: Decimal | None = None  # 10 = top 10% of the class

    @property
    def percent_of_best(self) -> Decimal:
        """obtained / best * 100. Only meaningful next to a check on `best`."""
        return self.obtained / self.best * 100


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
    year: int | None = Field(default=None, ge=1900, le=2100)
    qualified: bool | None = None  # as reported on the scorecard; no cutoff is invented


class FundsProof(Strict):
    """One proof of funds for the visa, as the mission pages name the routes."""

    route: Literal[
        "blocked_account", "declaration_of_commitment", "scholarship", "education_loan",
        "parental_income", "bank_guarantee",
    ]
    amount_eur: Decimal = Field(ge=0)


class Profile(Strict):
    schema_version: ProfileVersion = SCHEMA_VERSION
    # countries as English short names, as the university pages publish them ("India")
    citizenships: list[str] | None = None
    degree_country: str | None = None
    school_country: str | None = None
    degree_title: str | None = None
    degree_completed: bool | None = None
    total_credits: Decimal | None = None
    # "LP", "CP" or "ECTS credits" are entered as "ECTS" only by the student, who knows
    # what the transcript means; any other unit is "other" and is never converted
    credit_unit: Literal["ECTS", "other"] | None = None
    # student-confirmed credits per area, keyed in snake_case as the rules name them
    # (theoretical_cs, practical_cs, computer_engineering, mathematics, ...)
    subject_credits: dict[str, Decimal] | None = None
    grade: Grade | None = None
    language: list[LanguageEvidence] | None = None  # [] = student has no test
    english_instruction_share: Decimal | None = Field(default=None, ge=0, le=100)  # % of prior programme taught in English
    interview_passed: bool | None = None  # the target's aptitude interview, once taken (invited != passed)
    gre: Gre | NoTest | None = None  # None or Gre() = not supplied; "none" = has no GRE
    gate: Gate | NoTest | None = None
    german_level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] | None = None  # CEFR, as certified
    documents: list[str] | None = None  # document keys the student already has, e.g. "aps_certificate"
    funds_eur: Decimal | None = Field(default=None, ge=0)  # a total with no route; the visa rule reads `funds`
    # the university's written assessment of the degree (equivalence and subject allocation)
    # as the student reports it, per programme slug; only a reported "positive" can meet
    university_assessments: dict[str, Literal["positive", "negative"]] | None = None
    funds: list[FundsProof] | None = None  # [] = the student has no proof of funds yet
    visa_country: str | None = None  # where the student applies for the visa (the mission's country)

    @model_validator(mode="after")
    def _fields_match_version(self):
        if self.schema_version == "profile-v1" and "none" in (self.gre, self.gate):
            raise ValueError('"none" for gre or gate needs schema_version profile-v2')
        if self.schema_version in ("profile-v1", "profile-v2") and (self.funds is not None or self.visa_country is not None):
            raise ValueError("funds and visa_country need schema_version profile-v3")
        return self
