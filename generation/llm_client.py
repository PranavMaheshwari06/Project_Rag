"""Thin LLM wrapper — the only module that touches the OpenAI SDK. The SDK
talks to any OpenAI-compatible endpoint (`models.llm_base_url`, Gemini by
default). If no GEMINI_API_KEY is set, `available` is False and the answer generator uses the
extractive fallback instead. The key is read from the environment; never
hardcoded, never logged."""

from core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings):
        self.model = settings.models.llm_model
        self.base_url = settings.models.llm_base_url
        self._api_key = settings.llm_api_key
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def complete(self, messages: list[dict], json_mode: bool = False) -> str:
        if not self.available:
            raise RuntimeError("no LLM API key configured; use the extractive fallback")
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key, base_url=self.base_url)
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            **({"response_format": {"type": "json_object"}} if json_mode else {}),
        )
        return resp.choices[0].message.content or ""
