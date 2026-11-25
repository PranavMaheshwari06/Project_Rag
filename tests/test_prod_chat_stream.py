"""Phase 8 PR-F1: POST /chat/stream. One question, answered by one-shot or the agent, streamed as server-sent
events. Each event is produced in a thread-pool call that carries the request's context, so LLM calls inside the
stream are counted, hit the daily cap and respect the request deadline like any other request. No models, no key:
a fake pipeline and a scripted fake LLM."""

import asyncio
import json
import logging
import time

import pytest
from fastapi.testclient import TestClient

from agent.loop import agent_events, should_escalate
from agent.tools import Toolbox, ToolResult
from api.main import create_app
from core.config import load_settings
from core.exceptions import DeadlineError, UpstreamError
from core.logging import JsonFormatter, setup_logging
from core.metrics import record_call, request_deadline
from generation.prompt_builder import REFUSAL_TEXT, SYSTEM_PROMPT
from tests.test_prod_answer_contract import hits

ASK = {"query": "What is the TUM fee?"}
AGENT = {**ASK, "mode": "agent"}
SEARCH = '{"tool": "search_sources", "args": {"query": "fee"}}'
FINAL = '{"answer": "The fee is 85 EUR [1]."}'
GIVE_UP = json.dumps({"answer": REFUSAL_TEXT})
SECRET = "Marine Zoology Qwxyz"  # a profile value that must never reach the model or a log
PROFILE = {**AGENT, "profile": {"degree_title": SECRET, "degree_country": "India"}, "profile_confirmed": True,
           "intake": "winter", "starting_year": 2027}


class Pipeline:
    def __init__(self):
        self.calls = 0

    def search(self, query, mode="hybrid_rerank", top_k=None, timer=None, filters=None):
        self.calls += 1
        return hits()


class LLM:
    """Scripted replies; like LLMClient, it reports every provider request to the usage tracker."""

    available = True
    delay = 0.0  # seconds per call, for the disconnect test

    def __init__(self, *replies):
        self.replies, self.sent = list(replies), []

    def complete(self, messages, json_mode=False):
        record_call()
        self.sent.append(messages)
        time.sleep(self.delay)
        return self.replies.pop(0)


def events(response) -> list[tuple[str, dict]]:
    out = []
    for frame in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in frame.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


@pytest.fixture
def make(monkeypatch):
    def build(*replies, **serve):
        s = load_settings()
        for key, value in serve.items():
            setattr(s.serve, key, value)
        monkeypatch.setattr("api.main.get_settings", lambda: s)
        pipeline, llm = Pipeline(), LLM(*replies)
        for module in ("answer", "chat"):  # called directly, not through Depends
            monkeypatch.setattr(f"api.routes.{module}.get_retrieval_pipeline", lambda: pipeline)
            monkeypatch.setattr(f"api.routes.{module}.get_llm_client", lambda: llm)
        app = create_app()
        return app, TestClient(app), pipeline, llm

    return build


@pytest.fixture
def logs(monkeypatch):
    """Every log line, from any logger. create_app would drop a root handler, so set logging up once, here."""
    setup_logging()
    monkeypatch.setattr("api.main.setup_logging", lambda: None)
    records = []
    handler = logging.Handler()
    handler.emit = lambda record: records.append(json.loads(JsonFormatter().format(record)))
    logging.getLogger().addHandler(handler)
    yield records
    logging.getLogger().removeHandler(handler)


@pytest.fixture
def verdict(monkeypatch):
    """check_eligibility stubbed: records the toolbox it ran in, returns a verdict text."""
    seen = []

    def check(self, a):
        seen.append(self)
        return ToolResult(ok=True, text="headline: meets")

    monkeypatch.setattr("agent.tools.Toolbox.check_eligibility", check)
    return seen


def eligibility_call() -> str:
    slug = Toolbox(load_settings(), Pipeline()).programmes[0]
    return json.dumps({"tool": "check_eligibility", "args": {"programme": slug}})


# --- the agent as an event generator ---------------------------------------------------------------
def test_agent_events_yield_each_step_then_the_answer():
    out = list(agent_events("fee?", Toolbox(load_settings(), Pipeline()), LLM(SEARCH, FINAL)))
    assert [type(e).__name__ for e in out] == ["Step", "AgentAnswer"]
    assert out[0].tool == "search_sources" and out[-1].stop_reason == "answered"


def test_the_deadline_stops_the_agent_between_steps():
    llm = LLM(SEARCH, FINAL)
    with request_deadline(0.0), pytest.raises(DeadlineError):  # already past
        list(agent_events("fee?", Toolbox(load_settings(), Pipeline()), llm))
    assert llm.sent == []


# --- the route --------------------------------------------------------------------------------------
def test_oneshot_streams_sources_then_the_answer(make, logs):
    _, client, _, _ = make("The fee is 85 EUR [1].")
    r = client.post("/chat/stream", json=ASK)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache"
    (e1, sources), (e2, answer) = events(r)
    assert (e1, e2) == ("sources", "answer")
    assert sources["chunks"][0]["chunk_id"] == "c1" and sources["chunks"][0]["rerank_score"] == 0.9
    assert answer["text"] == "The fee is 85 EUR [1]." and not answer["refused"] and answer["answered_by"] == "oneshot"
    assert answer["citations"][0]["marker"] == 1 and answer["usage"]["llm_calls"] == 1
    end = [line for line in logs if line["msg"] == "stream"][-1]
    assert end["llm_calls"] == 1 and end["answered_by"] == "oneshot" and end["request_id"] == r.headers["x-request-id"]


def test_agent_streams_each_step_then_the_answer(make, logs):
    _, client, _, _ = make(SEARCH, FINAL)
    out = events(client.post("/chat/stream", json=AGENT))
    assert [name for name, _ in out] == ["step", "answer"]
    step, answer = out[0][1], out[1][1]
    assert step["tool"] == "search_sources" and step["markers"] == [1, 2] and step["ok"]
    assert answer["answered_by"] == "agent" and answer["text"] == "The fee is 85 EUR [1]."
    assert answer["usage"]["llm_calls"] == 2 and answer["citations"][0]["marker"] == 1
    end = [line for line in logs if line["msg"] == "stream"][-1]
    assert end["llm_calls"] == 2 and end["steps"] == 1 and end["refused"] is False


def test_the_daily_cap_ends_a_running_stream_with_an_error_event(make):
    app, client, _, _ = make(SEARCH, SEARCH, SEARCH, FINAL, daily_llm_calls=2)
    out = events(client.post("/chat/stream", json=AGENT))
    assert [name for name, _ in out] == ["step", "step", "error"]
    assert "demo quota reached" in out[-1][1]["detail"]
    assert app.state.limits.cap.used == 2  # the third call was refused, never sent


def test_the_request_deadline_ends_the_stream_with_an_error_event(make):
    _, client, _, llm = make(SEARCH, FINAL, request_deadline_s=0.0)
    out = events(client.post("/chat/stream", json=AGENT))
    assert out == [("error", {"detail": "the question took too long to answer; try a narrower one"})]
    assert llm.sent == []


def test_an_unexpected_failure_is_an_error_event_without_its_message(make, logs):
    _, client, pipeline, _ = make()
    message = " ".join(["secret", "detail", "from", "the", "question"])

    def boom(*a, **k):
        raise RuntimeError(message)

    pipeline.search = boom
    out = events(client.post("/chat/stream", json=ASK))
    assert out == [("error", {"detail": "something went wrong; try again"})]
    assert message not in json.dumps(logs)
    end = [line for line in logs if line["msg"] == "stream"][-1]
    assert end["error"] == "RuntimeError" and end["at"][-1].endswith(" boom")  # where, never what


def test_sources_are_sent_before_the_model_is_asked(make):
    _, client, _, llm = make()

    def down(*a, **k):
        raise UpstreamError("the language model is unavailable right now, try again later")

    llm.complete = down
    assert [name for name, _ in events(client.post("/chat/stream", json=ASK))] == ["sources", "error"]


def hang_up_after_the_first_event(app, payload) -> None:
    """Drive the app as uvicorn does (ASGI 2.3) with a client that disconnects once the first event arrives."""
    body = json.dumps(payload).encode()
    scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"}, "http_version": "1.1",
             "method": "POST", "scheme": "http", "path": "/chat/stream", "raw_path": b"/chat/stream",
             "root_path": "", "query_string": b"", "client": ("127.0.0.1", 1), "server": ("test", 80),
             "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]}

    async def run():
        first_event, requests = asyncio.Event(), [{"type": "http.request", "body": body, "more_body": False}]

        async def receive():
            if requests:
                return requests.pop()
            await first_event.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            if message.get("body"):
                first_event.set()

        await asyncio.wait_for(app(scope, receive, send), timeout=10)

    asyncio.run(run())


def test_a_client_that_hangs_up_stops_the_agent_and_is_still_logged(make, logs):
    app, _, _, llm = make(SEARCH, SEARCH, SEARCH, FINAL)
    llm.delay = 0.2
    hang_up_after_the_first_event(app, AGENT)
    (end,) = [line for line in logs if line["msg"] == "stream"]  # written by now, not at some later cleanup
    assert end["error"] == "ClientDisconnected" and end["request_id"] != "-"
    assert end["llm_calls"] == len(llm.sent) <= 2  # at most the call that was already running


def test_agent_mode_without_a_key_is_an_error_event(make):
    _, client, _, llm = make()
    llm.available = False
    (name, data), = events(client.post("/chat/stream", json=AGENT))
    assert name == "error" and "language model" in data["detail"]


# --- profile and cache ------------------------------------------------------------------------------
def test_a_profile_must_be_confirmed(make):
    _, client, _, _ = make()
    assert client.post("/chat/stream", json={**PROFILE, "profile_confirmed": False}).status_code == 422


def test_a_profile_reaches_only_the_eligibility_tool_and_no_log(make, logs, verdict):
    _, client, _, llm = make(eligibility_call(), '{"answer": "You meet it."}')
    client.post("/chat/stream", json=PROFILE)
    assert verdict and verdict[0].profile.degree_title == SECRET
    assert (verdict[0].intake, verdict[0].starting_year) == ("winter", 2027)
    assert SECRET not in json.dumps(llm.sent)  # the model sees the verdict, never the profile
    assert SECRET not in json.dumps(logs)


def test_answers_are_cached_per_mode(make):
    _, client, pipeline, llm = make("The fee is 85 EUR [1].", SEARCH, FINAL)
    client.post("/chat/stream", json=ASK)
    again = events(client.post("/chat/stream", json=ASK))
    assert again[-1][1]["cached"] and again[-1][1]["usage"]["llm_calls"] == 0 and pipeline.calls == 1
    assert client.post("/answer", json=ASK).json()["cached"]  # one-shot shares entries with /answer
    client.post("/chat/stream", json=AGENT)
    (name, data), = events(client.post("/chat/stream", json=AGENT))
    assert name == "answer" and data["cached"] and data["answered_by"] == "agent"
    assert len(llm.sent) == 3  # 1 one-shot + 2 agent; every repeat was free


def test_an_unreadable_agent_run_is_not_cached(make):
    _, client, _, llm = make("not json", "still not", "not json", "still not")
    client.post("/chat/stream", json=AGENT)
    (name, data), = events(client.post("/chat/stream", json=AGENT))
    assert data["refusal_reason"] == "bad_output" and not data["cached"] and len(llm.sent) == 4


def test_a_run_where_a_tool_crashed_is_not_cached(make):
    _, client, pipeline, llm = make(SEARCH, GIVE_UP, SEARCH, GIVE_UP)

    def boom(*a, **k):
        raise OSError("reranker could not load")

    pipeline.search = boom
    client.post("/chat/stream", json=AGENT)
    out = events(client.post("/chat/stream", json=AGENT))
    assert out[-1][1]["refusal_reason"] == "model" and not out[-1][1]["cached"] and len(llm.sent) == 4


def test_the_models_own_bad_arguments_do_not_stop_caching(make):
    bad = '{"tool": "get_requirements", "args": {"programme": "no-such-programme"}}'
    _, client, _, llm = make(bad, SEARCH, FINAL)
    client.post("/chat/stream", json=AGENT)
    (name, data), = events(client.post("/chat/stream", json=AGENT))
    assert data["cached"] and len(llm.sent) == 3


def test_a_request_with_a_profile_neither_writes_nor_reads_the_cache(make, verdict):
    oneshot = "The fee is 85 EUR [1]."
    with_profile = {**PROFILE, "mode": "oneshot"}
    app, client, _, llm = make(SEARCH, FINAL, oneshot, oneshot, SEARCH, FINAL, SEARCH, FINAL, oneshot,
                               llm_per_minute=100)
    client.post("/chat/stream", json=PROFILE)
    client.post("/chat/stream", json=with_profile)
    assert not app.state.answer_cache._data  # nothing written
    client.post("/chat/stream", json=ASK)
    client.post("/chat/stream", json=AGENT)
    for payload in (PROFILE, with_profile):  # the same questions are now cached without a profile
        assert not events(client.post("/chat/stream", json=payload))[-1][1]["cached"]
    assert len(llm.sent) == 9


def test_the_stream_has_the_llm_rate_limit(make):
    _, client, _, _ = make("The fee is 85 EUR [1].", llm_per_minute=1)
    assert client.post("/chat/stream", json=ASK).status_code == 200
    r = client.post("/chat/stream", json=ASK)
    assert r.status_code == 429 and "retry-after" in r.headers


# --- auto: one-shot first, the agent when one-shot refuses -------------------------------------------
AUTO = {**ASK, "mode": "auto"}
ANSWERED = "The fee is 85 EUR [1]."


def names(response) -> list[str]:
    return [name for name, _ in events(response)]


@pytest.mark.parametrize("reason,score,escalates", [
    ("model", 0.9, True), ("uncited", 0.9, True),
    ("gate", 0.02, True), ("gate", 0.019, False), ("gate", 0.0, False),
    ("guardrail", 0.9, False), ("extractive", 0.9, False), (None, 0.9, False),
])
def test_which_one_shot_outcomes_escalate(reason, score, escalates):
    assert should_escalate(reason, score, min_score=0.02) is escalates


def test_auto_keeps_an_answered_one_shot(make, logs):
    _, client, _, llm = make(ANSWERED)
    r = client.post("/chat/stream", json=AUTO)
    assert names(r) == ["sources", "answer"] and events(r)[-1][1]["answered_by"] == "oneshot"
    assert len(llm.sent) == 1
    assert [line for line in logs if line["msg"] == "stream"][-1]["escalated"] is False


def test_auto_hands_a_refused_question_to_the_agent(make, logs):
    _, client, _, _ = make(REFUSAL_TEXT, SEARCH, FINAL)
    out = events(client.post("/chat/stream", json=AUTO))
    assert [name for name, _ in out] == ["sources", "escalated", "step", "answer"]
    assert out[1][1] == {"refusal_reason": "model"}
    answer = out[-1][1]
    assert answer["answered_by"] == "agent" and not answer["refused"] and answer["usage"]["llm_calls"] == 3
    end = [line for line in logs if line["msg"] == "stream"][-1]
    assert end["escalated"] is True and end["llm_calls"] == 3 and end["answered_by"] == "agent"


@pytest.mark.parametrize("score,expected", [
    (0.001, ["sources", "answer"]),                         # out of scope: no agent calls
    (0.1, ["sources", "escalated", "step", "answer"]),      # in scope, ranked low
])
def test_auto_escalates_a_gate_refusal_only_above_the_cut(make, score, expected):
    _, client, pipeline, llm = make(SEARCH, GIVE_UP)
    searches = []

    def search(query, mode="hybrid_rerank", top_k=None, timer=None, filters=None):
        searches.append(query)
        return [rc.model_copy(update={"rerank_score": score if len(searches) == 1 else 0.9}) for rc in hits()]

    pipeline.search = search
    assert names(client.post("/chat/stream", json=AUTO)) == expected
    assert len(llm.sent) == (2 if "escalated" in expected else 0)


def test_auto_does_not_hand_a_guardrail_refusal_to_the_agent(make):
    _, client, _, llm = make(f"{SYSTEM_PROMPT} [1]")
    out = events(client.post("/chat/stream", json=AUTO))
    assert out[-1][1]["refusal_reason"] == "guardrail" and len(llm.sent) == 1


def test_auto_without_a_key_stays_one_shot(make):
    _, client, _, llm = make()
    llm.available = False
    out = events(client.post("/chat/stream", json=AUTO))
    assert [name for name, _ in out] == ["sources", "answer"] and out[-1][1]["answered_by"] == "oneshot"


def test_auto_ends_with_an_error_if_the_cap_stops_the_agent(make):
    _, client, _, _ = make(REFUSAL_TEXT, SEARCH, daily_llm_calls=2)
    assert names(client.post("/chat/stream", json=AUTO)) == ["sources", "escalated", "step", "error"]


def test_auto_repeats_are_served_from_the_cache(make):
    _, client, _, llm = make(REFUSAL_TEXT, SEARCH, FINAL)
    client.post("/chat/stream", json=AUTO)
    out = events(client.post("/chat/stream", json=AUTO))
    assert [name for name, _ in out] == ["sources", "escalated", "answer"]
    assert out[-1][1]["cached"] and out[-1][1]["usage"]["llm_calls"] == 0 and len(llm.sent) == 3
