"""Structured access log: one JSON line per request. Replaces uvicorn's plain access log.

Every line carries method, path, status, latency, and the request's LLM spend (calls, tokens, model).
Routes add a few more fields with `trace()`. The log never holds what a student typed or sent: only
lengths, counts, enumerated labels and timings, and no client address. `trace()` enforces that with a
whitelist of field names, so logging a new field is a deliberate edit here, not a side effect. The path is
logged only if it is one of our routes; anything else is "unmatched", because a client chose that text.

The same middleware sets up what every request needs from the outside: it tracks LLM usage, hooks the global
daily cap into every provider request, and sets the request deadline. The line is written even when the
route crashed (status 500), so a failing request is not invisible."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import log_event
from core.metrics import request_deadline, track_usage

log = logging.getLogger("api.access")

# ponytail: add a name here only when a route needs it; never a value that carries user text or a profile
_LOGGABLE = {"mode", "refused", "refusal_reason", "stages", "query_len", "n_targets", "text_len", "user_source_len",
             "cached"}


def trace(request, **fields) -> None:
    """Attach whitelisted fields to this request's access-log line."""
    unknown = set(fields) - _LOGGABLE
    if unknown:
        raise ValueError(f"not a loggable field: {sorted(unknown)}; add it to _LOGGABLE only if it holds no user data")
    request.state.trace.update(fields)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        limits = request.app.state.limits
        request.state.trace = {}
        status = 500  # what an unhandled error in the route becomes
        with track_usage(on_call=limits.cap.take) as usage, request_deadline(time.monotonic() + limits.deadline_s):
            try:
                response = await call_next(request)
                status = response.status_code
            finally:
                path = request.url.path if request.url.path in request.app.state.known_paths else "unmatched"
                log_event(
                    log,
                    "request",
                    method=request.method,
                    path=path,
                    status=status,
                    duration_ms=round((time.perf_counter() - start) * 1000, 1),
                    llm_calls=usage.calls,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    model=usage.model,
                    **request.state.trace,
                )
        return response
