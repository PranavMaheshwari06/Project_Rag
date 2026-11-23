import openai
import pytest

from core.config import Settings
from core.exceptions import UpstreamError
from core.metrics import track_usage
from generation import llm_client
from generation.llm_client import LLMClient, is_provider_error


class FakeOpenAI:
    calls: list[dict] = []

    def __init__(self, **kwargs):
        self.init = kwargs
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        FakeOpenAI.calls.append({"init": self.init, **kwargs})
        msg = type("M", (), {"content": "ok"})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def test_no_key_means_unavailable():
    assert not LLMClient(Settings()).available


def test_complete_uses_configured_endpoint(monkeypatch):
    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    settings = Settings(llm_api_key="test-key")
    assert LLMClient(settings).complete([{"role": "user", "content": "hi"}]) == "ok"
    call = FakeOpenAI.calls[-1]
    # max_retries=0: the SDK would silently re-send 429s and 5xx; the client owns retries
    assert call["init"] == {
        "api_key": "test-key", "base_url": settings.models.llm_base_url,
        "timeout": settings.models.llm_timeout_s, "max_retries": 0,
    }
    assert call["model"] == settings.models.llm_model
    assert call["temperature"] == 0


def test_quota_error_switches_to_fallback_model(monkeypatch):
    import openai

    class Quota(openai.RateLimitError):
        def __init__(self):
            pass

    class QuotaThenOk(FakeOpenAI):
        def create(self, **kwargs):
            if kwargs["model"] == "primary":
                raise Quota()
            return super().create(**kwargs)

    monkeypatch.setattr(openai, "OpenAI", QuotaThenOk)
    settings = Settings(llm_api_key="k")
    settings.models.llm_model = "primary"
    settings.models.llm_fallback_models = ["backup"]
    llm = LLMClient(settings)
    assert llm.complete([{"role": "user", "content": "hi"}]) == "ok"
    assert llm.model == "backup"


# --- Phase 8 PR-B: cool-down, retry, typed errors, usage -----------------------------------
HI = [{"role": "user", "content": "SECRET-PROMPT-TEXT"}]


class Quota(openai.RateLimitError):
    def __init__(self):
        pass


class Overloaded(openai.InternalServerError):  # a 503
    def __init__(self):
        self.status_code = 503


class Timeout(openai.APITimeoutError):
    def __init__(self):
        pass


class Rejected(openai.AuthenticationError):  # a 401: retrying or switching model cannot help
    def __init__(self):
        self.status_code = 401


class Retired(openai.NotFoundError):  # a model the provider has removed
    def __init__(self):
        self.status_code = 404


class QuotaAfter(openai.RateLimitError):  # a 429 that says when to come back
    def __init__(self, seconds):
        self.response = type("Resp", (), {"headers": {"retry-after": str(seconds)}})


class Scripted:
    """Fake SDK: `script[model]` is a list of outcomes (an exception to raise, or a usage tuple to return),
    consumed one per call; the last one repeats. Records (model) per call."""

    script: dict[str, list] = {}
    seen: list[str] = []
    on_call = None  # optional hook run at the start of every request

    def __init__(self, **kwargs):
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        model = kwargs["model"]
        Scripted.seen.append(model)
        if Scripted.on_call:
            Scripted.on_call()
        steps = Scripted.script[model]
        step = steps.pop(0) if len(steps) > 1 else steps[0]
        if isinstance(step, Exception):
            raise step
        if step == "no-choices":
            return type("R", (), {"choices": [], "usage": None})
        usage = None if step is None else type("U", (), {"prompt_tokens": step[0], "completion_tokens": step[1]})
        msg = type("M", (), {"content": "ok"})
        return type("R", (), {"choices": [type("C", (), {"message": msg})], "usage": usage})


@pytest.fixture
def world(monkeypatch):
    """A client over Scripted with a fake clock; `clock[0]` is 'now', sleeps are recorded."""
    clock, slept = [1000.0], []
    monkeypatch.setattr(openai, "OpenAI", Scripted)
    monkeypatch.setattr(llm_client, "_now", lambda: clock[0])
    monkeypatch.setattr(llm_client, "_sleep", slept.append)
    Scripted.script, Scripted.seen, Scripted.on_call = {}, [], None

    def make(primary, *fallbacks):
        settings = Settings(llm_api_key="k")
        settings.models.llm_model, settings.models.llm_fallback_models = primary, list(fallbacks)
        return LLMClient(settings)

    return make, clock, slept


def test_a_429_benches_the_model_then_it_returns_after_the_cooldown(world):
    make, clock, _ = world
    Scripted.script = {"a": [Quota(), (1, 1)], "b": [(1, 1)]}
    llm = make("a", "b")
    assert llm.complete(HI) == "ok" and llm.model == "b"
    assert Scripted.seen == ["a", "b"]

    llm.complete(HI)  # still benched: "a" is not tried again
    assert Scripted.seen == ["a", "b", "b"]

    clock[0] += llm._cooldown + 1  # the cool-down has passed: "a" is back and answers
    assert llm.complete(HI) == "ok" and llm.model == "a"
    assert Scripted.seen[-1] == "a"


def test_a_503_is_retried_once_after_a_backoff(world):
    make, _, slept = world
    Scripted.script = {"a": [Overloaded(), (1, 1)]}
    llm = make("a")
    assert llm.complete(HI) == "ok"
    assert Scripted.seen == ["a", "a"] and slept == [llm._backoff]


@pytest.mark.parametrize("failure", [Overloaded, Timeout])
def test_a_model_that_keeps_failing_hands_over_to_the_next(world, failure):
    make, _, slept = world
    Scripted.script = {"a": [failure()], "b": [(1, 1)]}
    llm = make("a", "b")
    assert llm.complete(HI) == "ok" and llm.model == "b"
    assert Scripted.seen == ["a", "a", "b"] and len(slept) == 1  # one retry on "a", none on "b"


def test_every_model_down_raises_a_typed_error_without_leaking_the_prompt(world):
    make, _, _ = world
    Scripted.script = {"a": [Overloaded()], "b": [Quota()]}
    with pytest.raises(UpstreamError) as err:
        make("a", "b").complete(HI)
    assert "SECRET-PROMPT-TEXT" not in err.value.message
    assert err.value.__context__ is None  # nothing chained: no provider exception rides along


def test_while_every_model_is_benched_no_request_is_sent(world):
    make, clock, _ = world
    Scripted.script = {"a": [Quota()]}
    llm = make("a")
    with pytest.raises(UpstreamError):
        llm.complete(HI)
    sent = len(Scripted.seen)
    with pytest.raises(UpstreamError):
        llm.complete(HI)
    assert len(Scripted.seen) == sent  # the demo's quota is not burned on calls that cannot succeed


def test_a_rejected_request_is_not_retried_or_rerouted(world):
    make, _, slept = world
    Scripted.script = {"a": [Rejected()], "b": [(1, 1)]}
    with pytest.raises(UpstreamError) as err:
        make("a", "b").complete(HI)
    assert Scripted.seen == ["a"] and slept == []
    assert err.value.__context__ is None  # the SDK error may echo the prompt: it must not ride along


def test_usage_is_summed_per_request_and_ignored_without_a_tracker(world):
    make, _, _ = world
    Scripted.script = {"a": [Overloaded(), (10, 3), (5, 2), None]}
    llm = make("a")
    with track_usage() as usage:
        llm.complete(HI)  # 503 attempt + the answered one
        llm.complete(HI)
        llm.complete(HI)  # the provider sent no usage block: the call still counts
    assert (usage.calls, usage.prompt_tokens, usage.completion_tokens) == (4, 15, 5)
    llm.complete(HI)  # outside a tracker: no error, nothing recorded
    with track_usage() as fresh:
        pass
    assert fresh.calls == 0


def test_upstream_error_counts_as_a_provider_error_for_the_harnesses():
    assert is_provider_error(UpstreamError("x"))
    assert not is_provider_error(ValueError("x"))


def test_a_429_that_says_retry_after_is_honoured(world):
    make, clock, _ = world
    Scripted.script = {"a": [QuotaAfter(10), (1, 1)], "b": [(1, 1)]}
    llm = make("a", "b")
    llm.complete(HI)
    assert llm._cooldown > 10  # the default is longer: the header won
    clock[0] += 11
    assert llm.complete(HI) == "ok" and llm.model == "a"


def test_a_retired_model_hands_over_to_the_next_without_a_retry(world):
    make, _, slept = world
    Scripted.script = {"a": [Retired()], "b": [(1, 1)]}
    llm = make("a", "b")
    assert llm.complete(HI) == "ok" and llm.model == "b"
    assert Scripted.seen == ["a", "b"] and slept == []


def test_an_empty_choices_list_is_a_provider_error_not_an_index_error(world):
    make, _, _ = world
    Scripted.script = {"a": ["no-choices"]}
    with pytest.raises(UpstreamError):
        make("a").complete(HI)


def test_the_overall_deadline_stops_retries_and_further_models(world):
    make, clock, _ = world
    Scripted.script = {"a": [Timeout()], "b": [(1, 1)]}
    Scripted.on_call = lambda: clock.__setitem__(0, clock[0] + 80)  # every request hangs 80 s
    with pytest.raises(UpstreamError):
        make("a", "b").complete(HI)
    assert "b" not in Scripted.seen  # the budget (90 s) was spent on "a"


def test_usage_names_the_model_that_answered_this_request(world):
    make, _, _ = world
    Scripted.script = {"a": [Quota()], "b": [(1, 1)]}
    with track_usage() as usage:
        make("a", "b").complete(HI)
    assert usage.model == "b"  # llm.model is shared by every request; this one is per request


def test_the_error_says_whether_it_was_quota_or_an_outage(world):
    make, _, _ = world
    Scripted.script = {"a": [Quota()]}
    with pytest.raises(UpstreamError) as quota:
        make("a").complete(HI)
    Scripted.script = {"a": [Overloaded()]}
    with pytest.raises(UpstreamError) as outage:
        make("a").complete(HI)
    assert "quota" in quota.value.message and "quota" not in outage.value.message
