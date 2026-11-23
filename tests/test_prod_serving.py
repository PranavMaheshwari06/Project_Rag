"""Phase 8 PR-A: liveness vs readiness, CORS from the environment, admin gate.
No models and no corpus: settings are fresh copies pointed at temp paths."""

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.config import load_settings


@pytest.fixture
def settings(tmp_path, monkeypatch):
    s = load_settings()
    s.paths.processed_path = str(tmp_path / "chunks.jsonl")
    s.paths.index_dir = str(tmp_path / "index")
    monkeypatch.setattr("api.routes.health.get_settings", lambda: s)
    monkeypatch.setattr("api.main.get_settings", lambda: s)
    return s


def test_health_is_liveness_only(settings):
    # up even with no corpus: a platform must not restart a container that is merely not ready
    r = TestClient(create_app()).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_is_503_until_corpus_and_both_indexes_exist(settings, tmp_path):
    client = TestClient(create_app())
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.json() == {
        "ready": False, "corpus_ingested": False, "bm25_index": False,
        "dense_index": False, "vector_backend": "memory",
    }

    (tmp_path / "chunks.jsonl").write_text("{}\n")
    (tmp_path / "index").mkdir()
    (tmp_path / "index" / "bm25.pkl").write_bytes(b"x")
    assert client.get("/ready").status_code == 503  # dense still missing

    (tmp_path / "index" / "dense.npz").write_bytes(b"x")
    r = client.get("/ready")
    assert r.status_code == 200 and r.json()["ready"] is True


def test_cors_origins_come_from_the_environment(settings, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.org, https://b.example.org")
    s = load_settings()
    assert s.serve.cors_origins == ["https://app.example.org", "https://b.example.org"]

    monkeypatch.setattr("api.main.get_settings", lambda: s)
    client = TestClient(create_app())
    ask = {"Access-Control-Request-Method": "GET"}
    ok = client.options("/health", headers={"Origin": "https://app.example.org", **ask})
    assert ok.headers.get("access-control-allow-origin") == "https://app.example.org"
    no = client.options("/health", headers={"Origin": "http://localhost:5173", **ask})
    assert "access-control-allow-origin" not in no.headers


def test_cors_defaults_to_local_dev(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert load_settings().serve.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


@pytest.mark.parametrize("path", ["/ingest", "/evaluate"])
def test_admin_routes_are_404_without_a_server_token(monkeypatch, path):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    # even a header that looks right opens nothing when no token is configured
    r = TestClient(create_app()).post(path, headers={"Authorization": "Bearer anything"})
    assert r.status_code == 404


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_admin_token_counts_as_unset(monkeypatch, blank):
    monkeypatch.setenv("ADMIN_TOKEN", blank)
    r = TestClient(create_app()).post("/ingest", headers={"Authorization": f"Bearer {blank}"})
    assert r.status_code == 404


@pytest.mark.parametrize("path", ["/ingest", "/evaluate"])
def test_admin_routes_reject_a_wrong_or_missing_token(monkeypatch, path):
    monkeypatch.setenv("ADMIN_TOKEN", "s3cret")
    client = TestClient(create_app())
    assert client.post(path).status_code == 401
    assert client.post(path, headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.post(path, headers={"Authorization": "s3cret"}).status_code == 401  # no scheme
    # non-ASCII must be a clean 401, not a TypeError 500
    assert client.post(path, headers={"Authorization": "Bearer café".encode("latin-1")}).status_code == 401


def test_admin_token_opens_the_gate(monkeypatch):
    # a bad body is 422 behind the gate; 422 (not 401/404) proves auth passed
    monkeypatch.setenv("ADMIN_TOKEN", "s3cret")
    r = TestClient(create_app()).post(
        "/ingest", headers={"Authorization": "Bearer s3cret"}, json={"rebuild_indexes": "not-a-bool"}
    )
    assert r.status_code == 422
