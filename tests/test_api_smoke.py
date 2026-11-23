"""Every endpoint answers with a 200 and a sane body. Uses the real sample
corpus + indexes built by the session fixture."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["corpus_ingested"] is True


def test_search(client):
    resp = client.post("/search", json={"query": "optional query parameters"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"], "expected at least one result"
    top = body["results"][0]
    assert top["rerank_score"] is not None
    assert top["chunk"]["chunk_id"]
    # registry provenance rides along on every chunk
    assert top["chunk"]["country"] == "XX" and top["chunk"]["layer"] == "rules"
    assert top["chunk"]["crawled_at"]
    assert "total" in body["latency_ms"]
    assert resp.headers["x-request-id"] == body["request_id"]


def test_search_modes(client):
    for mode in ("vector", "bm25", "hybrid"):
        resp = client.post("/search", json={"query": "middleware timing", "mode": mode})
        assert resp.status_code == 200, mode
        assert resp.json()["mode"] == mode


def test_search_rejects_empty_query(client):
    resp = client.post("/search", json={"query": ""})
    assert resp.status_code == 422


def test_answer(client):
    resp = client.post("/answer", json={"query": "How do I make a query parameter optional?"})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["refused"], bool)
    assert isinstance(body["citations"], list)
    assert body["chunks"]
    assert "generation" in body["latency_ms"]


ADMIN = {"Authorization": "Bearer test-admin"}


def test_ingest(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin")
    resp = client.post("/ingest", json={"rebuild_indexes": False}, headers=ADMIN)
    assert resp.status_code == 200
    body = resp.json()
    assert body["docs"] > 0
    assert body["chunks"] > 0


def test_evaluate(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin")
    resp = client.post("/evaluate", headers=ADMIN)
    assert resp.status_code == 200
    body = resp.json()
    assert [c["name"] for c in body["configs"]] == ["vector", "bm25", "hybrid", "hybrid_rerank"]
    assert body["gold_size"] > 0
