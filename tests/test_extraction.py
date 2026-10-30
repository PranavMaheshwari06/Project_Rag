import json

from core.config import Settings
from extraction.extract import ProgrammeSource, check_quotes, extract_programme
from extraction.schemas import ProgramRequirements

DOC = "## Admission\n\n- A bachelor's degree with at least **180 ECTS** is required.\n- Lectures are in English."
SRC = ProgrammeSource("Test Uni", "M.Sc. Testing", {"de/test/prog": DOC})


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, messages, json_mode=False):
        self.calls.append(messages)
        return self.replies.pop(0)


def stated(value, quote, doc_id="de/test/prog"):
    return {"status": "stated", "value": value, "quote": quote, "doc_id": doc_id}


def test_real_quote_kept_and_invented_one_dropped():
    reply = json.dumps({
        # markdown and case differ from the page; words match
        "min_total_ects": stated(180, "a Bachelor's degree with at least 180 ECTS is required"),
        "gre": "ignored extra key",
        "language_of_instruction": stated("English", "All courses are taught in English"),
        "semester_fee_eur": stated(300, "fee is 300", doc_id="de/other"),
    })
    rec, rejected = extract_programme(SRC, FakeLLM([reply]), Settings())
    assert rec.min_total_ects.value == 180
    assert rec.language_of_instruction.status == "not_published"
    assert rec.semester_fee_eur.status == "not_published"
    assert len(rejected) == 2
    assert rec.university == "Test Uni" and rec.source_doc_ids == ["de/test/prog"]


def test_invalid_reply_retried_once_with_the_error():
    bad = json.dumps({"min_total_ects": {"status": "stated", "value": 180}})  # no quote
    good = json.dumps({"min_total_ects": stated(180, "at least 180 ECTS is required")})
    llm = FakeLLM([bad, good])
    rec, _ = extract_programme(SRC, llm, Settings())
    assert rec.min_total_ects.value == 180
    assert len(llm.calls) == 2 and "invalid" in llm.calls[1][-1]["content"]


def test_every_supporting_citation_is_checked():
    field = stated(180, "at least 180 ECTS is required")
    field['supporting_citations'] = [{"quote": "Lectures are in English", "doc_id": "de/test/prog"}]
    rec = ProgramRequirements(university="u", programme="p", source_doc_ids=[], min_total_ects=field)
    assert check_quotes(rec, SRC.docs, 2) == []
    rec.min_total_ects.supporting_citations[0].quote = "invented supplemental evidence"
    assert "quote not found" in check_quotes(rec, SRC.docs, 2)[0]
    assert rec.min_total_ects.status == "not_published"
