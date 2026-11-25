"""Abuse and cost limits for a public demo. In memory, one worker: a restart resets the counters and a
second worker would double the allowance (fine for one container; a shared store is the upgrade).

- Per-client request windows (per minute and per day), a stricter pair for the routes that call the LLM.
- A global daily LLM-call cap: the cost ceiling in code, so spend stops whatever the provider budget alert does.
  It is enforced per provider request (see `DailyCap.take`), so a request that reaches it is cut off mid-way.
- Body-size cap: a POST must declare its length and stay under `serve.max_body_bytes`; chunked bodies are refused.
- Client address: the socket address, or the header named by `serve.client_ip_header` when a trusted edge
  (Cloudflare, a proxy) sets it. IPv6 is keyed by its /64. Counters hold only a salted hash of it; it is never logged.
All windows are fixed windows: a client can burst up to twice its allowance across a boundary."""

import hashlib
import ipaddress
import secrets
import threading
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.config import ServeCfg
from core.exceptions import TooManyRequestsError

_now = time.time  # module-level so tests can drive the clock
_SALT = secrets.token_bytes(16)  # per process: the hashes mean nothing outside it
MINUTE, DAY = 60, 86400
QUOTA_MSG = "demo quota reached for today, come back tomorrow (UTC)"
OVERFLOW = "~overflow"  # where new clients go once the table is full
MAX_CONTENT_LENGTH_DIGITS = 12  # about 1 TB: anything longer is malformed, and int() on thousands of digits raises


def _to_next(now: float, size: int) -> float:
    return size - now % size


class Window:
    """Fixed-window counters per key, for a per-minute and a per-day limit."""

    def __init__(self, per_minute: int, per_day: int, max_keys: int = 100_000):
        self.per_minute, self.per_day, self.max_keys = per_minute, per_day, max_keys
        self._hits: dict[str, list[int]] = {}  # key -> [minute id, hits, day id, hits]
        self._lock = threading.Lock()  # sync routes run in a thread pool
        self._calls = 0

    def hit(self, key: str) -> None:
        now = _now()
        minute, day = int(now // MINUTE), int(now // DAY)
        with self._lock:
            self._calls += 1
            if self._calls % 1000 == 0:  # drop yesterday's keys now and then
                self._hits = {k: v for k, v in self._hits.items() if v[2] == day}
            rec = self._hits.get(key)
            if rec is None and len(self._hits) >= self.max_keys:
                # a flood of distinct addresses must not grow memory without bound: late newcomers share one
                # bucket, so under attack they are limited together (fail safe) while known clients are unaffected
                key = OVERFLOW
                rec = self._hits.get(key)
            if rec is None or rec[2] != day:
                rec = self._hits[key] = [minute, 0, day, 0]
            if rec[0] != minute:
                rec[0], rec[1] = minute, 0
            if rec[3] >= self.per_day:
                raise TooManyRequestsError(QUOTA_MSG, _to_next(now, DAY))
            if rec[1] >= self.per_minute:
                raise TooManyRequestsError("too many requests, wait a minute and try again", _to_next(now, MINUTE))
            rec[1] += 1
            rec[3] += 1


class DailyCap:
    """Provider requests sent today (UTC), all clients together. `check` refuses an LLM request that has not
    started; `take` is called before every provider request it sends (core.metrics.record_call), so a request that
    reaches the cap is stopped at the next call. Overshoot is at most one call per request in flight."""

    def __init__(self, limit: int):
        self.limit, self.used, self._day = limit, 0, int(_now() // DAY)
        self._lock = threading.Lock()

    def _gate(self, spend: int) -> None:
        with self._lock:
            day = int(_now() // DAY)
            if day != self._day:
                self._day, self.used = day, 0
            if self.used >= self.limit:
                raise TooManyRequestsError(QUOTA_MSG, _to_next(_now(), DAY))
            self.used += spend

    def check(self) -> None:
        self._gate(0)

    def take(self) -> None:
        self._gate(1)


class Limits:
    def __init__(self, cfg: ServeCfg):
        self.any = Window(cfg.rate_per_minute, cfg.rate_per_day)
        self.llm = Window(cfg.llm_per_minute, cfg.llm_per_day)
        self.feedback = Window(cfg.feedback_per_day, cfg.feedback_per_day)
        self.cap = DailyCap(cfg.daily_llm_calls)
        self.ip_header = cfg.client_ip_header
        self.deadline_s = cfg.request_deadline_s


def client_ip(request: Request) -> str:
    header = request.app.state.limits.ip_header
    lines = request.headers.getlist(header) if header else []
    # behind one trusted edge the LAST header line, and the last non-empty entry of it, is what the edge
    # appended; everything to its left is written by the client
    entries = [e.strip() for e in lines[-1].split(",") if e.strip()] if lines else []
    return entries[-1] if entries else (request.client.host if request.client else "-")


def client_key(request: Request) -> str:
    ip = client_ip(request)
    try:
        addr = ipaddress.ip_address(ip)
        if addr.version == 6:
            addr = addr.ipv4_mapped or ipaddress.ip_network((addr, 64), strict=False)  # one household, one budget
        ip = str(addr)
    except ValueError:
        pass  # not an address: used as is
    return hashlib.blake2b(ip.encode(), key=_SALT, digest_size=8).hexdigest()


def limit_any(request: Request) -> None:
    """Dependency for the public routes that do not call the LLM."""
    request.app.state.limits.any.hit(client_key(request))


def limit_feedback(request: Request) -> None:
    """Dependency for /feedback: the general limits, then a small daily allowance of notes."""
    limit_any(request)
    request.app.state.limits.feedback.hit(client_key(request))


def limit_llm(request: Request) -> None:
    """Dependency for the routes that call the LLM: the cap first, so a refused request spends no allowance."""
    limits = request.app.state.limits
    limits.cap.check()
    key = client_key(request)
    limits.any.hit(key)
    limits.llm.hit(key)


class BodyLimitMiddleware(BaseHTTPMiddleware):
    """Chunked bodies are refused (411) because their framing ignores Content-Length under some HTTP parsers;
    a POST must declare a well-formed Content-Length (411 absent, 400 malformed) under the cap (413)."""

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request, call_next):
        if "transfer-encoding" in request.headers:
            return self._reject(request, 411, "chunked request bodies are not accepted; send a Content-Length")
        if request.method in ("POST", "PUT", "PATCH"):
            declared = request.headers.get("content-length")
            if declared is None:
                return self._reject(request, 411, "a Content-Length header is required")
            if not (declared.isascii() and declared.isdigit() and len(declared) <= MAX_CONTENT_LENGTH_DIGITS):
                return self._reject(request, 400, "invalid Content-Length")
            if int(declared) > self.max_bytes:
                return self._reject(request, 413, f"the request body is larger than {self.max_bytes} bytes")
        return await call_next(request)

    @staticmethod
    def _reject(request, status: int, detail: str) -> JSONResponse:
        return JSONResponse(status_code=status, content={
            "detail": detail, "request_id": getattr(request.state, "request_id", "-")})
