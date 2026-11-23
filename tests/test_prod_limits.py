"""Phase 8 PR-C: per-IP limits, the daily LLM-call cap, client-IP trust, body caps, the request
deadline and the access-log trace. No models, no key: a fake pipeline and a fake LLM client."""

import json
import logging
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_llm_client
from api.main import create_app
from api.middleware.logging_mw import trace
from core.config import load_settings
from core.logging import JsonFormatter
from core.metrics import record_call, request_deadline_at

START = 1_700_000_000.0  # a fixed instant; 80,000 s into its UTC day
TEXT = "I studied in India and finished a B.Tech with 180 ECTS."
PARSED = json.dumps({
    "profile": {"degree_country": "India", "total_credits": "180", "credit_unit": "ECTS"},
    "spans": {"degree_country": "studied in India", "total_credits": "180 ECTS", "credit_unit": "180 ECTS"},
})
PARSE = {"text": TEXT}
SEARCH = {"query": "x"}


class FakePipeline:
    def search(self, query, mode="hybrid_rerank", top_k=None, timer=None, filters=None):
        return []


class FakeLLM:
    """Stands in for LLMClient: records, per call, what the request context looked like."""

    available = True

    def __init__(self, calls_per_complete=1):
        self.calls_per_complete, self.sent, self.deadlines = calls_per_complete, [], []

    def complete(self, messages, json_mode=False):
        for _ in range(self.calls_per_complete):
            record_call()  # what LLMClient does for every request it sends
        self.sent.append(messages)
        self.deadlines.append(request_deadline_at())
        return PARSED


@pytest.fixture
def clock(monkeypatch):
    now = [START]
    monkeypatch.setattr("api.limits._now", lambda: now[0])
    return now


@pytest.fixture
def make(monkeypatch, clock):
    def build(llm=None, **serve):
        s = load_settings()
        for key, value in serve.items():
            setattr(s.serve, key, value)
        monkeypatch.setattr("api.main.get_settings", lambda: s)
        app = create_app()
        for route in ("search", "answer"):  # these routes call the function directly, not through Depends
            monkeypatch.setattr(f"api.routes.{route}.get_retrieval_pipeline", lambda: FakePipeline())
        app.dependency_overrides[get_llm_client] = lambda: llm or FakeLLM()
        return app, TestClient(app)

    return build


# --- per-IP limits ---------------------------------------------------------------------------
def test_over_the_minute_limit_is_429_with_retry_after_and_resets(make, clock):
    app, client = make(rate_per_minute=3)
    assert [client.post("/search", json=SEARCH).status_code for _ in range(3)] == [200, 200, 200]
    r = client.post("/search", json=SEARCH)
    assert r.status_code == 429
    assert 1 <= int(r.headers["retry-after"]) <= 60
    assert r.json()["request_id"] and "too many" in r.json()["detail"]
    clock[0] += 61
    assert client.post("/search", json=SEARCH).status_code == 200
    # the key is a salted hash: the raw address is never stored
    assert not any("testclient" in key for key in app.state.limits.any._hits)


def test_the_day_limit_says_demo_quota_and_resets_at_utc_midnight(make, clock):
    _, client = make(rate_per_minute=100, rate_per_day=2)
    assert client.post("/search", json=SEARCH).status_code == 200
    assert client.post("/search", json=SEARCH).status_code == 200
    r = client.post("/search", json=SEARCH)
    assert r.status_code == 429 and "demo quota reached" in r.json()["detail"]
    assert 1 <= int(r.headers["retry-after"]) <= 86400
    clock[0] += 86400
    assert client.post("/search", json=SEARCH).status_code == 200


def test_llm_routes_have_a_stricter_limit_of_their_own(make):
    _, client = make(llm_per_minute=2)
    assert [client.post("/profile/parse", json=PARSE).status_code for _ in range(2)] == [200, 200]
    assert client.post("/profile/parse", json=PARSE).status_code == 429
    assert client.post("/search", json=SEARCH).status_code == 200  # the cheap route is not affected


def test_health_and_ready_are_never_limited(make):
    _, client = make(rate_per_minute=1, rate_per_day=1)
    assert all(client.get("/health").status_code == 200 for _ in range(5))
    assert all(client.get("/ready").status_code in (200, 503) for _ in range(5))


# --- global daily LLM-call cap ---------------------------------------------------------------
def test_the_daily_cap_counts_real_calls_and_stops_llm_requests_only(make, clock):
    llm = FakeLLM(calls_per_complete=2)  # one request that needed a retry: 2 provider calls
    app, client = make(llm=llm, daily_llm_calls=2)
    assert client.post("/profile/parse", json=PARSE).status_code == 200
    assert app.state.limits.cap.used == 2
    r = client.post("/profile/parse", json=PARSE)
    assert r.status_code == 429 and "demo quota reached" in r.json()["detail"]
    assert len(llm.sent) == 1  # nothing was sent to the provider after the cap was reached
    assert client.post("/search", json=SEARCH).status_code == 200  # no LLM, no cap
    clock[0] += 86400
    assert client.post("/profile/parse", json=PARSE).status_code == 200


def test_the_cap_cuts_a_request_off_mid_way_instead_of_overshooting(make):
    llm = FakeLLM(calls_per_complete=3)  # a retry loop: the second provider call is over the cap
    app, client = make(llm=llm, daily_llm_calls=1)
    r = client.post("/profile/parse", json=PARSE)
    assert r.status_code == 429 and "demo quota reached" in r.json()["detail"]
    assert app.state.limits.cap.used == 1  # exactly the one call that was allowed, not three


# --- who the client is ----------------------------------------------------------------------
def test_a_forwarded_header_is_ignored_unless_configured(make):
    _, client = make(rate_per_minute=2)
    codes = [client.post("/search", json=SEARCH, headers={"X-Forwarded-For": f"10.0.0.{i}"}).status_code
             for i in range(3)]
    assert codes == [200, 200, 429]  # spoofing a header buys nothing by default


def test_a_configured_header_gives_each_client_its_own_budget_and_the_last_entry_counts(make):
    _, client = make(rate_per_minute=1, client_ip_header="X-Forwarded-For")

    def hit(xff):
        return client.post("/search", json=SEARCH, headers={"X-Forwarded-For": xff}).status_code

    assert hit("1.1.1.1") == 200
    assert hit("2.2.2.2") == 200  # a different client
    assert hit("1.1.1.1") == 429
    # the left entries are client-controlled; only the one the trusted edge appended counts
    assert hit("evil-a, 3.3.3.3") == 200
    assert hit("evil-b, 3.3.3.3") == 429


# --- body size ------------------------------------------------------------------------------
def test_an_oversized_body_is_413_and_a_body_without_length_is_411(make):
    _, client = make(max_body_bytes=200)
    assert client.post("/search", json=SEARCH).status_code == 200
    big = client.post("/search", json={"query": "y" * 300})
    assert big.status_code == 413 and big.json()["request_id"]
    chunked = client.post("/search", content=iter([b'{"query": "x"}']), headers={"content-type": "application/json"})
    assert chunked.status_code == 411


# --- request deadline -----------------------------------------------------------------------
def test_the_llm_call_sees_the_request_deadline(make):
    llm = FakeLLM()
    _, client = make(llm=llm, request_deadline_s=120.0)
    before = time.monotonic()
    assert client.post("/profile/parse", json=PARSE).status_code == 200
    assert before + 119 < llm.deadlines[0] < time.monotonic() + 121
    assert request_deadline_at() is None  # nothing leaks out of the request


# --- tracing --------------------------------------------------------------------------------
def capture(caplog):
    """create_app() calls setup_logging(), which clears the root handlers, pytest's capture included."""
    logging.getLogger().addHandler(caplog.handler)


def access_lines(caplog):
    return [r for r in caplog.records if r.name == "api.access"]


def test_the_access_line_carries_usage_and_trace_fields(make, caplog):
    _, client = make()
    capture(caplog)
    with caplog.at_level(logging.INFO):
        client.post("/profile/parse", json=PARSE)
        client.post("/search", json=SEARCH)
    parse, search = [r.extra_fields for r in access_lines(caplog)]
    assert parse["path"] == "/profile/parse" and parse["status"] == 200
    assert parse["llm_calls"] == 1 and parse["text_len"] == len(TEXT)
    assert search["llm_calls"] == 0 and search["mode"] == "hybrid_rerank"
    assert isinstance(search["stages"], dict) and search["query_len"] == 1


def test_no_profile_value_text_or_address_reaches_any_log_line(make, caplog):
    secret = "SENTINEL-4471-private"
    ip = "203.0.113.77"
    _, client = make(client_ip_header="X-Forwarded-For")
    capture(caplog)
    body = {
        "profile": {"degree_country": secret, "total_credits": "180", "credit_unit": "ECTS"},
        "profile_confirmed": True, "country": "Germany", "intake": "winter", "starting_year": 2027,
        "as_of": "2027-05-01", "targets": ["kit-m-sc-computer-science"],
    }
    headers = {"X-Forwarded-For": ip}
    with caplog.at_level(logging.DEBUG):
        client.post("/eligibility/check", json=body, headers=headers)
        client.post("/eligibility/check", json={**body, "targets": []}, headers=headers)  # a 422
        client.post("/profile/parse", json={"text": f"{TEXT} {secret}"}, headers=headers)
        client.post("/search", json={"query": secret}, headers=headers)
    assert access_lines(caplog), "the test must actually see the access log"
    rendered = "\n".join(JsonFormatter().format(r) for r in caplog.records)
    assert secret not in rendered
    assert ip not in rendered


def test_trace_refuses_a_field_that_is_not_on_the_whitelist():
    request = SimpleNamespace(state=SimpleNamespace(trace={}))
    trace(request, mode="llm", query_len=12)
    assert request.state.trace == {"mode": "llm", "query_len": 12}
    with pytest.raises(ValueError):
        trace(request, profile={"degree_country": "x"})  # a new loggable field is a deliberate decision


# --- review findings ------------------------------------------------------------------------
def test_chunked_encoding_is_rejected_even_with_a_content_length(make):
    # under h11 the chunked framing wins over a small declared length, which would skip the cap
    _, client = make(max_body_bytes=200)
    r = client.post("/search", content=b'{"query": "x"}',
                    headers={"transfer-encoding": "chunked", "content-length": "5"})
    assert r.status_code == 411


@pytest.mark.parametrize("declared", ["\u00b2".encode("latin-1"), pytest.param("9" * 5000, id="5000-digits"), "-1", "+5", "1.5"])
def test_a_malformed_content_length_is_400_not_a_crash(make, declared):
    _, client = make()
    r = client.post("/search", content=b"{}", headers={"content-length": declared})
    assert r.status_code == 400


def test_an_ipv6_client_is_limited_per_64_bit_prefix(make):
    _, client = make(rate_per_minute=1, client_ip_header="X-Forwarded-For")

    def hit(ip):
        return client.post("/search", json=SEARCH, headers={"X-Forwarded-For": ip}).status_code

    assert hit("2001:db8:1:1::1") == 200
    assert hit("2001:db8:1:1:ffff::9") == 429  # the same /64: one household, one budget
    assert hit("2001:db8:1:2::1") == 200  # another /64


def test_new_clients_share_one_bucket_once_the_table_is_full(make):
    app, client = make(rate_per_minute=1, client_ip_header="X-Forwarded-For")
    app.state.limits.any.max_keys = 2  # a flood of distinct addresses cannot grow memory without bound

    def hit(ip):
        return client.post("/search", json=SEARCH, headers={"X-Forwarded-For": ip}).status_code

    assert [hit("1.1.1.1"), hit("2.2.2.2"), hit("3.3.3.3")] == [200, 200, 200]  # the third lands in the overflow bucket
    assert hit("4.4.4.4") == 429  # ... which is now used up for everyone new
    assert hit("1.1.1.1") == 429 and len(app.state.limits.any._hits) <= 3


def test_duplicate_forwarded_headers_and_a_trailing_comma_cannot_pick_the_key(make):
    _, client = make(rate_per_minute=1, client_ip_header="X-Forwarded-For")

    def hit(headers):
        return client.post("/search", json=SEARCH, headers=headers).status_code

    two_lines = lambda first: [("X-Forwarded-For", first), ("X-Forwarded-For", "3.3.3.3")]  # noqa: E731
    assert hit(two_lines("evil-a")) == 200
    assert hit(two_lines("evil-b")) == 429  # the trusted edge's (last) line decides
    assert hit({"X-Forwarded-For": "9.9.9.9,"}) == 200  # an empty last entry falls back to the entry before it
    assert hit({"X-Forwarded-For": "9.9.9.9,"}) == 429


def test_the_request_id_is_bounded_and_the_path_is_not_attacker_text(make, caplog):
    _, client = make()
    capture(caplog)
    with caplog.at_level(logging.INFO):
        r = client.get("/health", headers={"X-Request-ID": "A" * 8000})
        ok = client.get("/health", headers={"X-Request-ID": "abc-123_X"})
        client.get("/no/such/page<script>")
    assert len(r.headers["x-request-id"]) == 12  # too long: a fresh id, not an echo
    assert ok.headers["x-request-id"] == "abc-123_X"
    assert [x.extra_fields["path"] for x in access_lines(caplog)][-1] == "unmatched"


def test_a_crashing_route_is_still_logged_and_its_calls_are_counted(make, monkeypatch, caplog):
    app, _ = make(daily_llm_calls=100)
    capture(caplog)

    class Boom:
        def search(self, *a, **k):
            raise RuntimeError("boom")

    monkeypatch.setattr("api.routes.search.get_retrieval_pipeline", lambda: Boom())
    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.INFO):
        assert client.post("/search", json=SEARCH).status_code == 500
    assert access_lines(caplog)[-1].extra_fields["status"] == 500
