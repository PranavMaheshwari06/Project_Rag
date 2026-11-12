from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

from retrieval.filters import KNOWN

from schemas.common import RetrievedChunk

SearchMode = Literal["vector", "bm25", "hybrid", "hybrid_rerank"]


def _known_values(filters: dict[str, list[str]]) -> dict[str, list[str]]:
    for key, values in filters.items():
        if unknown := sorted(set(values) - KNOWN[key]):
            raise ValueError(f"unknown {key} value(s): {unknown}")
    return filters


# chunk metadata field -> allowed values; see retrieval/filters.py for the semantics
Filters = Annotated[
    dict[Literal["university", "programme", "stage", "layer"],
         Annotated[list[Annotated[str, Field(min_length=1, max_length=100)]], Field(min_length=1, max_length=20)]],
    AfterValidator(_known_values)]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: SearchMode = "hybrid_rerank"
    top_k: int | None = Field(default=None, ge=1, le=50)
    filters: Filters | None = None


class SearchResponse(BaseModel):
    request_id: str
    query: str
    mode: SearchMode
    results: list[RetrievedChunk]
    latency_ms: dict[str, float]
