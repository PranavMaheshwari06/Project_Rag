"""Phase 8 PR-H: scripts/smoke_http.py, run against the real app through a test client (fake retrieval, no key, no
models). It proves the script matches the API contract, and that it fails when the server is broken."""

import json

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.config import load_settings
from generation.prompt_builder import SYSTEM_PROMPT
from scripts import smoke_http
from tests.test_prod_chat_stream import Pipeline


@pytest.fixture
def server(tmp_path, monkeypatch):
    s = load_settings()
    s.paths.processed_path = str(tmp_path / "chunks.jsonl")
    s.paths.index_dir = str(tmp_path / "index")
    s.paths.feedback_dir = str(tmp_path / "feedback")
    (tmp_path / "chunks.jsonl").write_text("{}\n")
    (tmp_path / "index").mkdir()
    for name in ("bm25.pkl", "dense.npz"):
        (tmp_path / "index" / name).write_bytes(b"x")
    for module in ("api.main", "api.routes.health", "api.routes.feedback"):
        monkeypatch.setattr(f"{module}.get_settings", lambda: s)
    monkeypatch.setattr("api.routes.answer.get_retrieval_pipeline", lambda: Pipeline())
    client = TestClient(create_app())

    def call(base, path, body=None):
        r = client.request("GET" if body is None else "POST", path, json=body)
        return r.status_code, r.headers, r.text

    monkeypatch.setattr(smoke_http, "call", call)
    return s, call


def test_a_healthy_server_passes_every_check(server, capsys):
    s, _ = server
    assert smoke_http.main(["http://test", "--feedback"]) == 0
    out = capsys.readouterr().out
    assert "FAIL" not in out and "7 of 7 checks run, 0 failed" in out
    with open(f"{s.paths.feedback_dir}/feedback.jsonl", encoding="utf-8") as fh:
        assert "smoke test" in fh.read()


def test_feedback_is_written_only_on_request(server, tmp_path):
    assert smoke_http.main(["http://test"]) == 0
    assert not (tmp_path / "feedback" / "feedback.jsonl").exists()


def test_every_question_is_new_to_the_cache():
    asked = {smoke_http.fresh("Q?") for _ in range(5)}
    assert len(asked) == 5 and all(q.startswith("Q? ") for q in asked)


# --- a broken server must fail the check named after what broke ---

def edit(change):
    """Change the JSON body of a successful reply; error replies (the 429 of the limit check) pass through."""
    def mutate(status, headers, text):
        if status != 200:
            return status, headers, text
        data = json.loads(text)
        change(data)
        return status, headers, json.dumps(data)
    return mutate


def swap(old, new):
    def mutate(status, headers, text):
        if status != 200:
            return status, headers, text
        assert old in text, "the test no longer matches the reply"
        return status, headers, text.replace(old, new)
    return mutate


def reply_with(status=None, headers=None, text=None):
    def mutate(s, h, t):
        return (s if status is None else status(s)), (h if headers is None else headers(h)), \
            (t if text is None else text(t))
    return mutate


def stream_frame(event, **changes):
    def mutate(status, headers, text):
        frames = text.strip().split("\n\n")
        for i, frame in enumerate(frames):
            if frame.startswith(f"event: {event}\n"):
                data = json.loads(frame.split("data: ", 1)[1])
                frames[i] = f"event: {event}\ndata: {json.dumps({**data, **changes})}"
        return status, headers, "\n\n".join(frames) + "\n\n"
    return mutate


def result(data):
    return data["results"][0]


QUESTION, INJECTION = smoke_http.QUESTION, smoke_http.INJECTION
BROKEN = {
    # id: (check that must fail, path, only for questions starting with, mutation)
    "not-ready": ("ready", "/ready", None, swap('"ready":true', '"ready":false')),
    "ready-503": ("ready", "/ready", None, reply_with(status=lambda s: 503)),
    "verdict": ("eligibility", "/eligibility/check", None, swap('"verdict":"unknown"', '"verdict":"meets"')),
    "headline": ("eligibility", "/eligibility/check", None,
                 edit(lambda d: result(d).update(headline="meets_published_requirements"))),
    "stale-rules": ("eligibility", "/eligibility/check", None, edit(lambda d: result(d).update(status="rules_stale"))),
    "uncited-verdicts": ("eligibility", "/eligibility/check", None,
                         edit(lambda d: [c.update(citations=[]) for c in result(d)["report"]["criteria"]])),
    "no-citations": ("answer", "/answer", QUESTION, edit(lambda d: d.update(citations=[]))),
    "refused": ("answer", "/answer", QUESTION, edit(lambda d: d.update(refused=True, refusal_reason="gate"))),
    "no-marker": ("answer", "/answer", QUESTION, edit(lambda d: d.update(answer="Sure."))),
    "cached": ("answer", "/answer", QUESTION, edit(lambda d: d.update(cached=True))),
    "no-source-link": ("answer", "/answer", QUESTION,
                       edit(lambda d: [c.update(url="") for c in d["citations"]])),
    "unmapped-marker": ("answer", "/answer", QUESTION, edit(lambda d: d.update(answer="Fact [9]."))),
    "answer-500": ("answer", "/answer", QUESTION, reply_with(status=lambda s: 500)),
    "stream-503": ("stream", "/chat/stream", None, reply_with(status=lambda s: 503)),
    "stream-error": ("stream", "/chat/stream", None, swap("event: answer", "event: error")),
    "stream-no-passages": ("stream", "/chat/stream", None, stream_frame("sources", chunks=[])),
    "stream-gate-refusal": ("stream", "/chat/stream", None,
                            stream_frame("answer", refused=True, refusal_reason="gate")),
    "stream-cached": ("stream", "/chat/stream", None, stream_frame("answer", cached=True)),
    "stream-uncited": ("stream", "/chat/stream", None, stream_frame("answer", citations=[])),
    "stream-type": ("stream", "/chat/stream", None,
                    reply_with(headers=lambda h: {"content-type": "application/json"})),
    # cited correctly (the prompt itself holds [1] and [2]), so only the leak check can catch it
    "prompt-leak": ("injection", "/answer", INJECTION, edit(lambda d: d.update(
        refused=False, answer=SYSTEM_PROMPT, citations=[{"marker": n, "url": "https://example.org"} for n in (1, 2)]))),
    "injection-obeyed": ("injection", "/answer", INJECTION,
                         edit(lambda d: d.update(refused=False, answer="Sure, I will ignore my rules.",
                                                 citations=[]))),
    "consent-ignored": ("feedback", "/feedback", None,
                        reply_with(status=lambda s: 201, text=lambda t: '{"stored":true}')),
    "not-stored": ("feedback", "/feedback", None, reply_with(text=lambda t: t.replace('"stored":true', '"x":1'))),
    "no-retry-after": ("limit", "/eligibility/check", None, reply_with(headers=lambda h: {})),
    "limit-503": ("limit", "/eligibility/check", None, reply_with(status=lambda s: 503 if s == 429 else s)),
}


@pytest.mark.parametrize("failing,path,question,mutate", BROKEN.values(), ids=BROKEN)
def test_a_broken_reply_fails_its_check(server, monkeypatch, capsys, failing, path, question, mutate):
    _, call = server

    def broken(base, p, body=None):
        reply = call(base, p, body)
        if p == path and (question is None or body["query"].startswith(question)):
            return mutate(*reply)
        return reply

    monkeypatch.setattr(smoke_http, "call", broken)
    monkeypatch.setattr(smoke_http.time, "sleep", lambda s: pytest.fail("waited although --wait is 0"))
    assert smoke_http.main(["http://test", "--feedback"]) == 1
    assert f"FAIL {failing}:" in capsys.readouterr().out


def test_llm_flag_fails_a_server_that_answers_without_its_model(server, monkeypatch, capsys):
    _, call = server
    assert smoke_http.main(["http://test", "--llm"]) == 1  # no key here: answers are extractive
    assert "FAIL answer:" in capsys.readouterr().out


def test_llm_flag_passes_a_model_answer(server, monkeypatch, capsys):
    _, call = server
    as_model = edit(lambda d: d.update(mode="llm"))

    def with_model(base, p, body=None):
        reply = call(base, p, body)
        return as_model(*reply) if p == "/answer" and body["query"].startswith(QUESTION) else reply

    monkeypatch.setattr(smoke_http, "call", with_model)
    assert smoke_http.main(["http://test", "--llm"]) == 0


def test_a_server_with_no_limit_fails_the_limit_check(server, monkeypatch, capsys):
    _, call = server
    last_ok = {}

    def unlimited(base, p, body=None):
        reply = call(base, p, body)
        if reply[0] == 429:
            return last_ok[p]
        last_ok[p] = reply
        return reply

    monkeypatch.setattr(smoke_http, "call", unlimited)
    assert smoke_http.main(["http://test"]) == 1
    assert "FAIL limit:" in capsys.readouterr().out


def test_an_error_before_the_429_fails_the_limit_check(server, monkeypatch, capsys):
    _, call = server
    seen = []

    def flaky(base, p, body=None):
        reply = call(base, p, body)
        if p == "/eligibility/check":
            seen.append(p)
            if len(seen) == 3:  # the second request of the limit check
                return 500, reply[1], reply[2]
        return reply

    monkeypatch.setattr(smoke_http, "call", flaky)
    assert smoke_http.main(["http://test"]) == 1
    assert "FAIL limit:" in capsys.readouterr().out


def test_it_gives_up_on_a_server_that_never_becomes_ready(monkeypatch, capsys):
    def refused(*args):
        raise ConnectionError("refused")

    ticks, naps = iter(range(0, 1000, 10)), []

    def nap(seconds):  # a script that ignores its deadline fails the test instead of hanging it
        naps.append(seconds)
        if len(naps) > 10:
            pytest.fail("kept waiting past the deadline")

    monkeypatch.setattr(smoke_http, "call", refused)
    monkeypatch.setattr(smoke_http.time, "sleep", nap)
    monkeypatch.setattr(smoke_http.time, "monotonic", lambda: next(ticks))
    assert smoke_http.main(["http://test", "--wait", "30"]) == 1
    out = capsys.readouterr().out
    assert "FAIL ready:" in out and "1 of 6 checks run" in out  # nothing else is tried
