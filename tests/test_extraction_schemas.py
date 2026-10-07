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
