"""Structured access log: one JSON line per request with method, path, status
and wall-clock latency. Replaces uvicorn's plain access log."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import log_event

log = logging.getLogger("api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        log_event(
            log,
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=elapsed_ms,
        )
        return response
