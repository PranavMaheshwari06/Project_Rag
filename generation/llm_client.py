"""Thin LLM wrapper — the only module that touches the OpenAI SDK. The SDK
talks to any OpenAI-compatible endpoint (`models.llm_base_url`, Gemini by
default). If no GEMINI_API_KEY is set, `available` is False and the answer generator uses the
extractive fallback instead. The key is read from the environment; never
hardcoded, never logged.

Failure handling (the client owns it; the SDK's own retries are off, so every request sent is counted):
- 429: that model is benched (the provider's Retry-After, else `models.llm_cooldown_s`), then tried again;
  the next model answers meanwhile.
- 5xx or timeout: one retry after `models.llm_backoff_s`, then the next model.
- 404 (a retired model): the next model, no retry.
- any other provider error (401, 400...): retrying or switching cannot help, raise at once.
- `models.llm_deadline_s` caps one `complete()` call: no new attempt starts after it.
- nothing answered: `UpstreamError` with a fixed message, because provider errors can echo the prompt."""

import logging
import time

from core.config import Settings
from core.exceptions import UpstreamError
from core.metrics import record_call, record_model, record_tokens

log = logging.getLogger(__name__)
_now = time.monotonic  # module-level so tests can drive the clock
_sleep = time.sleep


class _EmptyReply(Exception):
    """The provider answered with no choices at all: treated like an outage of that model."""


def _retry_after(exc) -> float | None:
    try:
        return float(exc.response.headers["retry-after"])
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


class LLMClient:
    def __init__(self, settings: Settings):
        m = settings.models
        # the model that answered last: shared by every request on this client, so only reliable in
        # single-threaded callers (scripts, harnesses); per request, read `Usage.model` from track_usage
        self.model = m.llm_model
        self._models = [m.llm_model, *m.llm_fallback_models]
        self._benched: dict[str, float] = {}  # model -> time it may be used again
        self._cooldown, self._backoff = m.llm_cooldown_s, m.llm_backoff_s
        self._timeout, self._deadline = m.llm_timeout_s, m.llm_deadline_s
        self.base_url = m.llm_base_url
        self._api_key = settings.llm_api_key
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def complete(self, messages: list[dict], json_mode: bool = False) -> str:
        if not self.available:
            raise RuntimeError("no LLM API key configured; use the extractive fallback")
        import openai

        if self._client is None:
            self._client = openai.OpenAI(
                api_key=self._api_key, base_url=self.base_url, timeout=self._timeout, max_retries=0
            )
        deadline = _now() + self._deadline
        rejected = False
        for model in self._models:
            if _now() >= deadline:
                log.warning("llm deadline of %.0fs reached before model %s", self._deadline, model)
                break
            if self._benched.get(model, 0.0) > _now():
                continue
            try:
                text = self._send(model, messages, json_mode, deadline)
            except openai.RateLimitError as e:
                wait = min(max(_retry_after(e) or self._cooldown, 1.0), 3600.0)
                self._benched[model] = _now() + wait
                log.warning("llm model %s benched for %.0fs after a 429", model, wait)
                continue
            except (openai.InternalServerError, openai.APIConnectionError, _EmptyReply) as e:  # 5xx, timeout, network
                log.warning("llm model %s failed twice (%s), trying the next", model, type(e).__name__)
                continue
            except openai.NotFoundError:
                log.error("llm model %s was not found: retired or misspelled, trying the next", model)
                continue
            except openai.APIError as e:
                log.error("llm request to %s rejected (%s %s)", model, type(e).__name__, getattr(e, "status_code", "-"))
                rejected = True  # raised below, outside this handler, so the SDK error is not chained
                break
            self.model = model
            record_model(model)
            return text
        if rejected:
            raise UpstreamError("the language model rejected the request")
        if any(until > _now() for until in self._benched.values()):
            log.warning("llm: no model answered; benched until %s", sorted(round(u - _now()) for u in self._benched.values()))
            raise UpstreamError("the language model's quota is used up for now, try again later")
        raise UpstreamError("the language model is unavailable right now, try again later")

    def _send(self, model: str, messages: list[dict], json_mode: bool, deadline: float) -> str:
        import openai

        for attempt in (0, 1):
            record_call()
            try:
                resp = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0,
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                )
            except (openai.InternalServerError, openai.APIConnectionError):
                if attempt == 1 or _now() + self._backoff >= deadline:
                    raise
                _sleep(self._backoff)
                continue
            record_tokens(getattr(resp, "usage", None))
            if not resp.choices:
                raise _EmptyReply
            content = resp.choices[0].message.content
            if not content:
                # ponytail: an empty reply (e.g. safety-blocked) is returned as "" as before; rejecting it is
                # the answer contract in PR-D 6a, and the agent loop already repairs it
                log.warning("llm model %s returned empty content (finish_reason=%s)", model,
                            getattr(resp.choices[0], "finish_reason", "-"))
            return content or ""


def is_provider_error(exc: BaseException) -> bool:
    """True for errors raised by the SDK (quota, overload, timeout) or by this client when no model
    could answer, so callers can stop on those and still let their own bugs raise."""
    return isinstance(exc, UpstreamError) or type(exc).__module__.split(".")[0] == "openai"
