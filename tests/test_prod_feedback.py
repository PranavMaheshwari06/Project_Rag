"""POST /feedback: a note about an answer, stored only with consent, without a profile or an address, and removed
after the retention period. No models."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.config import load_settings
from core.logging import JsonFormatter, setup_logging

NOTE = "The TUM deadline Qwxyz looks out of date."
GOOD = {"request_id": "a1b2c3d4e5f6", "doc_id": "de/tum/informatics/page", "note": NOTE, "consent": True}


@pytest.fixture
def make(monkeypatch, tmp_path):
    def build(**serve):
        s = load_settings()
        s.paths.feedback_dir = str(tmp_path / "feedback")
        for key, value in serve.items():
            setattr(s.serve, key, value)
        for module in ("api.main", "api.routes.feedback"):
            monkeypatch.setattr(f"{module}.get_settings", lambda: s)
        return TestClient(create_app()), tmp_path / "feedback" / "feedback.jsonl"

    return build


def rows(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def aged(days: int, note: str) -> str:
    at = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
    return json.dumps({"at": at, "answer_request_id": "x", "doc_id": None, "note": note}) + "\n"


def test_a_note_is_stored_with_nothing_else_about_the_sender(make):
    client, path = make()
    r = client.post("/feedback", json=GOOD)
    assert r.status_code == 201 and r.json() == {"stored": True, "kept_days": 90}
    [row] = rows(path)
    assert set(row) == {"at", "answer_request_id", "doc_id", "note"}
    assert (row["answer_request_id"], row["doc_id"], row["note"]) == (GOOD["request_id"], GOOD["doc_id"], NOTE)


def test_notes_are_kept_one_per_line_whatever_characters_they_hold(make):
    client, path = make()
    odd = "line one\nline two three é"
    for note in (odd, "second"):
        assert client.post("/feedback", json={**GOOD, "doc_id": None, "note": note}).status_code == 201
    assert [row["note"] for row in rows(path)] == [odd, "second"]


@pytest.mark.parametrize("change", [
    {"consent": False}, {"consent": "yes"}, {"consent": 1}, {"consent": None},
    {"note": ""}, {"note": "   "}, {"note": "x" * 501},
    {"request_id": "has spaces"}, {"request_id": "x" * 65}, {"doc_id": "../../etc/passwd"},
    {"profile": {"degree_country": "India"}}, {"email": "someone@example.org"},
])
def test_anything_else_is_refused_and_not_stored_or_echoed(make, change):
    client, path = make()
    r = client.post("/feedback", json={**GOOD, **change})
    assert r.status_code == 422 and not path.exists()
    assert "Qwxyz" not in r.text and "example.org" not in r.text and "xxxx" not in r.text


def test_consent_has_to_be_sent(make):
    client, path = make()
    assert client.post("/feedback", json={k: v for k, v in GOOD.items() if k != "consent"}).status_code == 422
    assert not path.exists()


def test_old_and_unreadable_lines_are_removed_on_the_next_note(make):
    client, path = make()
    path.parent.mkdir(parents=True)
    path.write_text(aged(91, "old") + aged(89, "recent") + "not json\n", encoding="utf-8")
    client.post("/feedback", json=GOOD)
    assert [row["note"] for row in rows(path)] == ["recent", NOTE]


def test_old_notes_are_removed_at_startup_and_no_file_is_made_for_nothing(make):
    _, path = make()
    assert not path.exists()
    path.parent.mkdir(parents=True)
    path.write_text(aged(91, "old") + aged(1, "recent"), encoding="utf-8")
    make()
    assert [row["note"] for row in rows(path)] == ["recent"]


def test_a_full_box_refuses_new_notes(make):
    client, path = make(feedback_max_entries=1)
    assert client.post("/feedback", json=GOOD).status_code == 201
    r = client.post("/feedback", json=GOOD)
    assert r.status_code == 429 and r.headers["retry-after"] and len(rows(path)) == 1


def test_the_per_client_limit_applies(make):
    client, _ = make(rate_per_minute=1)
    assert [client.post("/feedback", json=GOOD).status_code for _ in range(2)] == [201, 429]


def test_a_store_that_cannot_be_written_says_so(make):
    client, path = make()
    path.parent.parent.mkdir(parents=True, exist_ok=True)
    path.parent.write_text("a file where the folder should be", encoding="utf-8")
    r = client.post("/feedback", json=GOOD)
    assert r.status_code == 503 and "Qwxyz" not in r.text


def test_one_client_cannot_fill_the_box(make):
    client, _ = make(feedback_per_day=2)
    assert [client.post("/feedback", json=GOOD).status_code for _ in range(3)] == [201, 201, 429]


def test_a_half_written_file_is_removed_at_startup(make):
    _, path = make()
    path.parent.mkdir(parents=True)
    path.with_suffix(".tmp").write_text(aged(91, "left by a crash"), encoding="utf-8")
    make()
    assert not path.with_suffix(".tmp").exists()


def refuse(*args, **kwargs):
    raise PermissionError("no")


def test_a_failed_write_keeps_the_old_notes(make, monkeypatch):
    client, path = make()
    client.post("/feedback", json=GOOD)
    monkeypatch.setattr("api.routes.feedback.os.replace", refuse)
    assert client.post("/feedback", json={**GOOD, "note": "second"}).status_code == 503
    assert [row["note"] for row in rows(path)] == [NOTE]


def test_an_unreadable_store_keeps_its_notes_and_does_not_stop_startup(make, monkeypatch):
    client, path = make()
    client.post("/feedback", json=GOOD)
    before, read = path.read_bytes(), Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: refuse() if self == path else read(self, *a, **k))
    assert client.post("/feedback", json={**GOOD, "note": "second"}).status_code == 503
    make()
    assert path.read_bytes() == before


def test_the_browser_may_read_the_answer_id_that_feedback_needs(make):
    client, _ = make()
    r = client.get("/health", headers={"origin": "http://localhost:5173"})
    assert "x-request-id" in r.headers.get("access-control-expose-headers", "").lower()


def test_the_note_is_never_logged(make, monkeypatch):
    setup_logging()
    monkeypatch.setattr("api.main.setup_logging", lambda: None)
    lines = []
    handler = logging.Handler()
    handler.emit = lambda record: lines.append(JsonFormatter().format(record))
    logging.getLogger().addHandler(handler)
    try:
        client, _ = make()
        client.post("/feedback", json=GOOD)
        client.post("/feedback", json={**GOOD, "consent": False})
    finally:
        logging.getLogger().removeHandler(handler)
    assert any('"path": "/feedback"' in line for line in lines) and "Qwxyz" not in "".join(lines)
