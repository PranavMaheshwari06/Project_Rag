"""Per-request latency tracking plus a couple of small numeric helpers used by
the evaluation harness."""

import time
from contextlib import contextmanager


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
