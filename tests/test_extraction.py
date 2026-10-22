import json

from core.config import Settings
from extraction.extract import ProgrammeSource, extract_programme

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
