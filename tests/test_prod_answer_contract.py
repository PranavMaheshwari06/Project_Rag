"""Phase 8 PR-D 6a: every answer is cited or it is not given. One-shot makes at most one repair call
before refusing, and says why it refused. No models, no key: fake retrieval and a scripted fake LLM.
The agent's side of the contract is in tests/test_agent.py."""

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.config import load_settings
from generation.answer_generator import generate_answer
from generation.prompt_builder import REFUSAL_TEXT, REPAIR_CITE
from schemas.common import Chunk, RetrievedChunk


def hits(score=0.9, n=2):
    return [RetrievedChunk(chunk=Chunk(chunk_id=f"c{i}", doc_id=f"d{i}", source=f"d{i}", title=f"t{i}",
                                       section_path="s", url="https://example.org", text=f"Fact number {i} is about the programme.",
                                       token_count=3), rerank_score=score)
            for i in range(1, n + 1)]


class ScriptedLLM:
    """Returns canned replies in order and records every message list it was sent."""

    available = True

    def __init__(self, *replies):
        self.replies, self.sent = list(replies), []

    def complete(self, messages, json_mode=False):
        self.sent.append([dict(m) for m in messages])
        return self.replies.pop(0)


@pytest.fixture
def settings():
    return load_settings()


def test_a_cited_reply_is_the_answer_in_one_call(settings):
    llm = ScriptedLLM("It is 180 ECTS [1].")
    draft = generate_answer("q", hits(), settings, llm)
    assert not draft.refused and draft.refusal_reason is None and draft.mode == "llm"
    assert draft.text == "It is 180 ECTS [1]." and len(llm.sent) == 1


@pytest.mark.parametrize("first", ["It is 180 ECTS.", "", "It is 180 ECTS [7]."])
def test_an_uncited_empty_or_out_of_range_reply_gets_one_repair(settings, first):
    llm = ScriptedLLM(first, "It is 180 ECTS [2].")
    draft = generate_answer("q", hits(), settings, llm)
    assert not draft.refused and draft.text == "It is 180 ECTS [2]." and len(llm.sent) == 2
    repair = llm.sent[1]
    # the repair resends the evidence, shows the failed reply and asks for markers
    assert repair[:2] == llm.sent[0] and repair[2] == {"role": "assistant", "content": first}
    assert repair[3] == {"role": "user", "content": REPAIR_CITE}


def test_two_uncited_replies_give_the_refusal_with_reason_uncited(settings):
    llm = ScriptedLLM("It is 180 ECTS.", "Still 180 ECTS.")
    draft = generate_answer("q", hits(), settings, llm)
    assert draft.refused and draft.refusal_reason == "uncited" and draft.text == REFUSAL_TEXT
    assert draft.mode == "refusal" and len(llm.sent) == 2  # one repair, never a loop


def test_the_model_refusing_after_the_repair_is_a_model_refusal(settings):
    draft = generate_answer("q", hits(), settings, ScriptedLLM("No idea.", REFUSAL_TEXT))
    assert draft.refused and draft.refusal_reason == "model"


def test_the_refusal_text_is_a_model_refusal_with_no_repair(settings):
    llm = ScriptedLLM(f"  {REFUSAL_TEXT}\n")
    draft = generate_answer("q", hits(), settings, llm)
    assert draft.refused and draft.refusal_reason == "model" and len(llm.sent) == 1


def test_a_low_score_is_a_gate_refusal_with_no_call(settings):
    llm = ScriptedLLM()
    draft = generate_answer("q", hits(score=0.0), settings, llm)
    assert draft.refused and draft.refusal_reason == "gate" and llm.sent == []
    assert generate_answer("q", [], settings, llm).refusal_reason == "gate"


def test_the_extractive_fallback_is_unchanged(settings):
    class NoKey:
        available = False

    draft = generate_answer("fact number", hits(), settings, NoKey())
    assert not draft.refused and draft.refusal_reason is None and draft.mode == "extractive" and "[1]" in draft.text


def test_the_answer_route_returns_the_refusal_reason(settings, monkeypatch):
    monkeypatch.setattr("api.main.get_settings", lambda: settings)
    app = create_app()
    pipeline = type("P", (), {"search": lambda self, *a, **k: hits()})()
    monkeypatch.setattr("api.routes.answer.get_retrieval_pipeline", lambda: pipeline)
    llm = ScriptedLLM("No marker.", "No marker again.", "Cited [1].")
    monkeypatch.setattr("api.routes.answer.get_llm_client", lambda: llm)
    client = TestClient(app)
    body = client.post("/answer", json={"query": "q"}).json()
    assert body["refused"] and body["refusal_reason"] == "uncited" and body["citations"] == []
    body = client.post("/answer", json={"query": "q"}).json()
    assert not body["refused"] and body["refusal_reason"] is None and [c["marker"] for c in body["citations"]] == [1]
