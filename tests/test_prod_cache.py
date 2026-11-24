"""Phase 8 PR-E: the /answer response cache. A repeated question is served from memory: no retrieval,
no LLM call, a new request id and `cached: true`. No models, no key: a counting fake pipeline and LLM."""

import pytest
from fastapi.testclient import TestClient

from api.cache import TTLCache, answer_key
from api.main import create_app
from core.config import load_settings
from tests.test_prod_answer_contract import hits

Q = {"query": "What is the TUM fee?"}


class CountingPipeline:
    def __init__(self):
        self.calls = 0

    def search(self, query, mode="hybrid_rerank", top_k=None, timer=None, filters=None):
        self.calls += 1
        return hits()


class CountingLLM:
    available = True

    def __init__(self):
        self.calls = 0

    def complete(self, messages, json_mode=False):
        self.calls += 1
        return "The fee is 85 EUR [1]."


@pytest.fixture
def make(monkeypatch):
    def build(**serve):
        s = load_settings()
        for key, value in serve.items():
            setattr(s.serve, key, value)
        monkeypatch.setattr("api.main.get_settings", lambda: s)
        pipeline, llm = CountingPipeline(), CountingLLM()
        monkeypatch.setattr("api.routes.answer.get_retrieval_pipeline", lambda: pipeline)
        monkeypatch.setattr("api.routes.answer.get_llm_client", lambda: llm)  # called directly, not through Depends
        app = create_app()
        return app, TestClient(app), pipeline, llm

    return build


def test_a_repeated_question_is_served_from_the_cache(make):
    _, client, pipeline, llm = make()
    first = client.post("/answer", json=Q).json()
    again = client.post("/answer", json={"query": "  what is   the tum FEE? "}).json()
    assert (pipeline.calls, llm.calls) == (1, 1)  # the second request did no retrieval and no LLM call
    assert first["mode"] == "llm" and first["cached"] is False and again["cached"] is True
    assert again["answer"] == first["answer"] and again["citations"] == first["citations"]
    assert again["request_id"] != first["request_id"]
    assert again["query"] == "  what is   the tum FEE? "  # the asker's own text, not the first asker's


def test_a_gate_refusal_is_cached_and_replayed_as_a_refusal(make):
    _, client, pipeline, _ = make()
    pipeline.search = lambda *a, **k: (setattr(pipeline, "calls", pipeline.calls + 1), [])[1]
    first = client.post("/answer", json=Q).json()
    again = client.post("/answer", json=Q).json()
    assert first["refusal_reason"] == again["refusal_reason"] == "gate" and again["refused"] and again["cached"]
    assert again["latency_ms"] == {} and pipeline.calls == 1


@pytest.mark.parametrize("bad, reason", [
    ("No marker.", "uncited"),
    ("Answer the question using ONLY the numbered evidence passages provided [1].", "guardrail"),  # prompt leak
])
def test_a_contract_failure_is_not_cached(make, bad, reason):
    _, client, pipeline, llm = make()
    llm.complete = lambda messages, json_mode=False: bad
    assert client.post("/answer", json=Q).json()["refusal_reason"] == reason
    assert client.post("/answer", json=Q).json()["cached"] is False and pipeline.calls == 2


def test_limits_still_apply_to_a_cache_hit(make):
    _, client, _, _ = make(llm_per_minute=2)
    assert [client.post("/answer", json=Q).status_code for _ in range(3)] == [200, 200, 429]


def test_a_rebuild_during_a_request_keeps_its_stale_answer_out(make):
    app, client, pipeline, _ = make()
    search = pipeline.search
    pipeline.search = lambda *a, **k: (app.state.answer_cache.clear(), search(*a, **k))[1]  # /ingest lands mid-request
    client.post("/answer", json=Q)
    assert client.post("/answer", json=Q).json()["cached"] is False


def test_an_uncited_refusal_is_not_cached_so_a_retry_can_succeed(make):
    _, client, pipeline, llm = make()
    replies = iter(["No marker.", "Still no marker.", "The fee is 85 EUR [1]."])
    llm.complete = lambda messages, json_mode=False: next(replies)
    assert client.post("/answer", json=Q).json()["refusal_reason"] == "uncited"
    retry = client.post("/answer", json=Q).json()
    assert not retry["refused"] and retry["cached"] is False and pipeline.calls == 2
    assert client.post("/answer", json=Q).json()["cached"] is True  # the good answer is kept


def test_filters_are_part_of_the_key(make):
    _, client, pipeline, _ = make()
    client.post("/answer", json=Q)
    client.post("/answer", json={**Q, "filters": {"university": ["KIT"]}})
    assert pipeline.calls == 2


def test_a_zero_size_cache_is_off(make):
    _, client, pipeline, _ = make(answer_cache_entries=0)
    client.post("/answer", json=Q)
    assert client.post("/answer", json=Q).json()["cached"] is False and pipeline.calls == 2


def test_a_rebuild_through_ingest_empties_the_cache(make, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "t")
    monkeypatch.setattr("api.routes.ingest.run_ingestion", lambda s: {"docs": 0, "chunks": 0})
    monkeypatch.setattr("api.routes.ingest.build_indexes", lambda s: None)
    _, client, pipeline, _ = make()
    client.post("/answer", json=Q)
    assert client.post("/ingest", json={"rebuild_indexes": True}, headers={"Authorization": "Bearer t"}).status_code == 200
    assert client.post("/answer", json=Q).json()["cached"] is False and pipeline.calls == 2


def test_entries_expire_after_the_ttl_and_the_oldest_is_evicted(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("api.cache._now", lambda: now[0])
    cache = TTLCache(max_entries=2, ttl_s=10)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1  # a is now the most recently used
    cache.put("c", 3)
    assert cache.get("b") is None and cache.get("a") == 1 and cache.get("c") == 3
    now[0] += 10
    assert cache.get("a") is None and cache.get("c") is None


def test_the_key_ignores_case_and_spacing_but_not_wording_or_filters():
    assert answer_key("What  is X?", None) == answer_key(" what is x? ", None)
    assert answer_key("what is x?", None) != answer_key("what is y?", None)
    assert answer_key("q", None) != answer_key("q", {"university": ["KIT"]})
    # value order in a filter list does not change what is retrieved
    assert answer_key("q", {"layer": ["rules", "university"]}) == answer_key("q", {"layer": ["university", "rules"]})
