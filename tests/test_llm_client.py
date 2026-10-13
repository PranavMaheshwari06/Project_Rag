from core.config import Settings
from generation.llm_client import LLMClient


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
    assert call["init"] == {"api_key": "test-key", "base_url": settings.models.llm_base_url}
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
