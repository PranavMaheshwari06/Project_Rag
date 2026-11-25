"""POST /feedback: a student's note about an answer, for the maintainer to read. It is stored only with consent, as
one JSON line holding the time, the answer's request id, an optional source id and the note: no profile and no
client address. Lines older than `serve.feedback_retention_days` are removed at startup and whenever a note arrives
(docs/privacy-notice.md). The note is never logged.

ponytail: one file rewritten under a process lock, enough for one worker and a few thousand notes; a second worker
or real traffic needs a database."""

import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from api.limits import DAY, limit_feedback
from core.config import get_settings
from core.exceptions import ServiceUnavailableError, TooManyRequestsError

log = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(limit_feedback)])
_lock = threading.Lock()  # sync routes run in a thread pool


class Feedback(BaseModel):
    model_config = ConfigDict(extra="forbid")  # no field for a profile or a contact detail: an extra one is refused

    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")  # the x-request-id of the answer
    doc_id: str | None = Field(default=None, pattern=r"^[a-z0-9/_-]{1,200}$")  # a source the note is about
    note: str = Field(min_length=1, max_length=500)
    consent: StrictBool

    @field_validator("note")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("note is empty")
        return value

    @field_validator("consent")
    @classmethod
    def _given(cls, value: bool) -> bool:
        if not value:
            raise ValueError("a note is stored only with consent: true")
        return value


def _path() -> Path:
    settings = get_settings()
    return settings.resolve(settings.paths.feedback_dir) / "feedback.jsonl"


def _kept(path: Path, days: int) -> list[str]:
    """The stored lines still inside the retention period. A line whose age cannot be read is dropped, because it
    would otherwise be kept for ever."""
    if not path.is_file():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    kept, unreadable = [], 0
    for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
        if not line:
            continue
        try:
            if datetime.fromisoformat(json.loads(line)["at"]) >= cutoff:
                kept.append(line)
        except (ValueError, KeyError, TypeError, RecursionError):
            unreadable += 1
    if unreadable:
        log.warning("dropped %d unreadable feedback lines", unreadable)
    return kept


def _write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)  # a crash mid-write leaves the old file whole


def purge() -> None:
    """Remove expired notes at startup. A store that cannot be rewritten is reported, not fatal: answering questions
    does not depend on it."""
    try:
        with _lock:
            path = _path()
            path.with_suffix(".tmp").unlink(missing_ok=True)  # a note half written before a crash
            if path.is_file():
                _write(path, _kept(path, get_settings().serve.feedback_retention_days))
    except OSError as e:
        log.error("expired feedback could not be removed: %s", type(e).__name__)


@router.post("/feedback", status_code=201)
def feedback(body: Feedback) -> dict:
    cfg = get_settings().serve
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "answer_request_id": body.request_id,
             "doc_id": body.doc_id, "note": body.note}
    try:
        with _lock:
            path = _path()
            lines = _kept(path, cfg.feedback_retention_days)
            full = len(lines) >= cfg.feedback_max_entries
            _write(path, lines if full else [*lines, json.dumps(entry)])  # ASCII: one note, one line
    except OSError as e:
        log.error("feedback could not be stored: %s", type(e).__name__)
        raise ServiceUnavailableError("feedback cannot be saved right now") from None
    if full:
        raise TooManyRequestsError("the feedback box is full; try again another day", DAY)
    return {"stored": True, "kept_days": cfg.feedback_retention_days}
