import pytest
from pydantic import ValidationError

from extraction.schemas import Cited, ProgramRequirements


def test_stated_needs_quote_and_doc():
    with pytest.raises(ValidationError):
        Cited[int](status="stated", value=180)
    ok = Cited[int](status="stated", value=180, quote="180 ECTS", doc_id="de/x")
    assert ok.value == 180


def test_not_published_must_be_empty():
    with pytest.raises(ValidationError):
        Cited[int](status="not_published", value=180)


def test_record_defaults_to_not_published_and_round_trips():
    rec = ProgramRequirements(university="TUM", programme="M.Sc. Informatics", source_doc_ids=["de/x"])
    assert rec.entrance_tests.status == "not_published"
    assert ProgramRequirements.model_validate_json(rec.model_dump_json()) == rec


def test_test_name_spellings_are_normalised():
    from extraction.schemas import EntranceTest, LanguageTest

    assert EntranceTest(test="GRE General Test", requirement="one_of").test == "GRE"
    assert EntranceTest(test="Indian GATE test", requirement="one_of").test == "GATE"
    assert LanguageTest(test="TOEFL iBt", min_score="88").test == "TOEFL iBT"
    assert LanguageTest(test="PTE Academic", min_score="60").test == "PTE Academic"


def test_conditional_exam_and_degree_origin_round_trip():
    from extraction.schemas import Deadline, EntranceTest

    exam = EntranceTest(test="Entrance Exam", requirement="required", condition="Only if documents are insufficient")
    deadline = Deadline(intake="winter", applicant_group="non_eu", date="31 May", degree_origin="outside_germany")
    assert EntranceTest.model_validate_json(exam.model_dump_json()).condition == exam.condition
    assert deadline.degree_origin == "outside_germany"
    assert Deadline(intake="winter", applicant_group="all", date="15 July").degree_origin is None
    with pytest.raises(ValidationError):
        Deadline(intake="winter", applicant_group="all", date="15 July", degree_origin="EU")


def test_supporting_citations_require_stated_field_and_complete_citation():
    with pytest.raises(ValidationError):
        Cited[str](supporting_citations=[{"quote": "a source", "doc_id": "x"}])
    with pytest.raises(ValidationError):
        Cited[str](status="stated", value="x", quote="a source", doc_id="x",
                   supporting_citations=[{"quote": "", "doc_id": "y"}])
