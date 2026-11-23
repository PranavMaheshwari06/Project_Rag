"""Per-request latency tracking plus a couple of small numeric helpers used by
the evaluation harness."""

import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class Usage:
    """LLM spend of one request: provider requests sent (retries and failures included) and tokens."""

    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str | None = None  # the model that answered (the last one, if a request made several calls)


_usage: ContextVar[Usage | None] = ContextVar("llm_usage", default=None)


@contextmanager
def track_usage():
    """Everything the LLM client sends inside this block is added to the yielded Usage. Outside a
    block nothing is recorded. A contextvar, so concurrent requests never mix their numbers."""
    usage = Usage()
    token = _usage.set(usage)
    try:
        yield usage
    finally:
        _usage.reset(token)


def record_call() -> None:
    if (u := _usage.get()) is not None:
        u.calls += 1


def record_model(model: str) -> None:
    if (u := _usage.get()) is not None:
        u.model = model


def record_tokens(provider_usage) -> None:
    """`provider_usage` is the SDK's usage block or None (some endpoints omit it)."""
    if (u := _usage.get()) is not None and provider_usage is not None:
        u.prompt_tokens += getattr(provider_usage, "prompt_tokens", 0) or 0
        u.completion_tokens += getattr(provider_usage, "completion_tokens", 0) or 0


class StageTimer:
    """Collects wall-clock latency per pipeline stage for a single request."""

    def __init__(self):
        self.stages: dict[str, float] = {}

    @contextmanager
    def track(self, stage: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.stages[stage] = self.stages.get(stage, 0.0) + elapsed_ms

    @property
    def total_ms(self) -> float:
        return sum(self.stages.values())

    def as_dict(self) -> dict[str, float]:
        out = {name: round(ms, 1) for name, ms in self.stages.items()}
        out["total"] = round(self.total_ms, 1)
        return out


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile; enough precision for latency reporting."""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def rough_token_count(text: str) -> int:
    """~4 chars per token; used only for cost reporting, not budgeting."""
    return max(1, len(text) // 4)
