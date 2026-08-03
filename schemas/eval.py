from pydantic import BaseModel


class ConfigMetrics(BaseModel):
    name: str
    recall: dict[str, float]  # {"@5": 0.9, "@10": 1.0}
    mrr: float
    ndcg: dict[str, float]
    latency_p50_ms: float
    latency_p95_ms: float


class AnswerMetrics(BaseModel):
    groundedness: float
    unsupported_claim_rate: float
    refusal_rate: float
    method: str  # heuristic vs llm-judge, so nobody mistakes one for the other


class BenchmarkResult(BaseModel):
    generated_at: str
    gold_size: int
    chunk_count: int
    settings_snapshot: dict[str, int | float | str]
    configs: list[ConfigMetrics]
    answers: AnswerMetrics | None = None
