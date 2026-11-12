from pydantic import BaseModel, Field

from schemas.common import RetrievedChunk
from schemas.search import Filters


class AnswerRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    filters: Filters | None = None


class Citation(BaseModel):
    marker: int
    chunk_id: str
    url: str
    title: str
    section_path: str


class AnswerResponse(BaseModel):
    request_id: str
    query: str
    answer: str
    refused: bool
    mode: str  # "llm" | "extractive" | "refusal"
    citations: list[Citation]
    chunks: list[RetrievedChunk]
    latency_ms: dict[str, float]
