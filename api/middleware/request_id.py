"""Assigns every request an id (or honors an incoming X-Request-ID) and puts
it in a contextvar so every log line in the request's lifetime carries it."""

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("x-request-id") or uuid4().hex[:12]
        request.state.request_id = rid
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = rid
            return response
        finally:
            request_id_var.reset(token)
