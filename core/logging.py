"""Structured JSON logging. Every line carries the current request_id (set by
the request middleware via a contextvar) so log lines can be joined per request."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_var.get(),
            "msg": record.getMessage(),
        }
        fields = getattr(record, "extra_fields", None)
        if fields:
            entry.update(fields)
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
    # our middleware logs requests with latency; uvicorn's plain access log just duplicates it
    logging.getLogger("uvicorn.access").disabled = True


def log_event(logger: logging.Logger, msg: str, **fields) -> None:
    """Log with arbitrary structured fields attached."""
    logger.info(msg, extra={"extra_fields": fields})
