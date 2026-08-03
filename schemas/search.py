from typing import Literal

from pydantic import BaseModel, Field

from schemas.common import RetrievedChunk

SearchMode = Literal["vector", "bm25", "hybrid", "hybrid_rerank"]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: SearchMode = "hybrid_rerank"
    top_k: int | None = Field(default=None, ge=1, le=50)


class SearchResponse(BaseModel):
    request_id: str
    query: str
    mode: SearchMode
    results: list[RetrievedChunk]
    latency_ms: dict[str, float]
