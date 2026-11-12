from pydantic import BaseModel, Field


class ConfigMetrics(BaseModel):
    name: str
    recall: dict[str, float]  # {"@5": 0.9, "@10": 1.0}
    mrr: float
    ndcg: dict[str, float]
    latency_p50_ms: float
    latency_p95_ms: float
    query_count: int = 0
    # 95% bootstrap intervals over queries; empty when not computed
    recall_ci: dict[str, tuple[float, float]] = Field(default_factory=dict)
    mrr_ci: tuple[float, float] | None = None


class AnswerMetrics(BaseModel):
    groundedness: float
    unsupported_claim_rate: float
    refusal_rate: float
    method: str  # heuristic vs llm-judge, so nobody mistakes one for the other
    generation_mode: str = "extractive"
    refusal_confusion: dict = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    generated_at: str
    gold_size: int
    chunk_count: int
    settings_snapshot: dict[str, int | float | str]
    configs: list[ConfigMetrics]
    answers: AnswerMetrics | None = None
    total_gold_size: int = 0
    gold_counts: dict[str, int] = Field(default_factory=dict)
    reviewer_counts: dict[str, int] = Field(default_factory=dict)
    retrieval_by_kind: dict[str, list[ConfigMetrics]] = Field(default_factory=dict)
    extraction: dict[str, dict] = Field(default_factory=dict)
    audit: dict | None = None
    refusal_calibration: dict = Field(default_factory=dict)
    input_hashes: dict[str, str] = Field(default_factory=dict)
