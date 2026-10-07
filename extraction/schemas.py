"""Records the LLM extracts from programme pages and a human verifies.

Every requirement is a `Cited` field: either `stated` with a value, a verbatim
quote and the doc it came from, or `not_published`. There is no "probably":
if the page doesn't say it, the field is not_published and the eligibility
engine reports it as unknown instead of guessing."""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class Cited(BaseModel, Generic[T]):
    status: Literal["stated", "not_published"] = "not_published"
    value: T | None = None
    quote: str | None = None  # verbatim span from the source text
    doc_id: str | None = None  # registry id of the page the quote is from

    @model_validator(mode="after")
    def _consistent(self):
        filled = [self.value is not None, bool(self.quote), bool(self.doc_id)]
        if self.status == "stated" and not all(filled):
            raise ValueError("a stated field needs value, quote and doc_id")
        if self.status == "not_published" and any(filled):
            raise ValueError("a not_published field must be empty")
        return self


class SubjectCredits(BaseModel):
    area: str  # e.g. "mathematics", "computer science"
    min_ects: int


class LanguageTest(BaseModel):
    test: str  # e.g. "IELTS", "TOEFL iBT", "CEFR"
    min_score: str  # kept as text: 6.5, 88 and C1 are all valid minimums


class Deadline(BaseModel):
    intake: Literal["winter", "summer"]
    applicant_group: Literal["all", "eu", "non_eu"]
    date: str  # as published, e.g. "31 May"


class EntranceTest(BaseModel):
    test: str  # e.g. "GRE", "GATE", "TUM aptitude assessment"
    min_scores: str | None = None  # as published: "QR above 75th percentile"
    requirement: Literal["required", "one_of", "recommended"]  # one_of = any of the one_of tests
    applies_to_degree_countries: list[str] = []  # empty = all applicants


class GermanRequirement(BaseModel):
    min_level: Literal["none", "A1", "A2", "B1", "B2", "C1", "C2"]
    needed_by: Literal["admission", "enrolment", "during_studies"]


class ProgramRequirements(BaseModel):
    university: str
    programme: str
    source_doc_ids: list[str]

    degree_requirement: Cited[str] = Cited()  # e.g. "Bachelor in CS or a related field"
    min_total_ects: Cited[int] = Cited()
    subject_credits: Cited[list[SubjectCredits]] = Cited()
    min_grade_german_scale: Cited[float] = Cited()  # 1.0 best, 4.0 pass
    english: Cited[list[LanguageTest]] = Cited()
    entrance_tests: Cited[list[EntranceTest]] = Cited()
    german: Cited[GermanRequirement] = Cited()
    work_experience: Cited[Literal["required", "counts_in_selection", "recommended", "not_required"]] = Cited()
    aps_required: Cited[bool] = Cited()
    application_route: Cited[Literal["direct", "uni_assist", "both"]] = Cited()
    deadlines: Cited[list[Deadline]] = Cited()
    selection_process: Cited[str] = Cited()  # aptitude assessment, interview, essay...
    required_documents: Cited[list[str]] = Cited()
    tuition_eur_per_semester_non_eu: Cited[float] = Cited()
    semester_fee_eur: Cited[float] = Cited()
    language_of_instruction: Cited[str] = Cited()

    verified: bool = False  # flipped by a human on the review screen
