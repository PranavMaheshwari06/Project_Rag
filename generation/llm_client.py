"""Thin LLM wrapper — the only module that touches the OpenAI SDK. If no
OPENAI_API_KEY is set, `available` is False and the answer generator uses the
extractive fallback instead. The key is read from the environment; never
hardcoded, never logged."""

from core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings):
        self.model = settings.models.llm_model
        self._api_key = settings.openai_api_key
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def complete(self, messages: list[dict]) -> str:
        if not self.available:
            raise RuntimeError("no LLM API key configured; use the extractive fallback")
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        resp = self._client.chat.completions.create(
            model=self.model, messages=messages, temperature=0
        )
        return resp.choices[0].message.content or ""
