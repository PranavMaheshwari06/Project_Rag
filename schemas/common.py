"""Shared models used across ingestion, retrieval and the API layer."""

from pydantic import BaseModel


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    source: str
    title: str
    section_path: str
    url: str
    text: str
    token_count: int


class RetrievedChunk(BaseModel):
    """A chunk plus its full score trace through the retrieval pipeline.
    Scores are None for stages the chunk didn't pass through."""

    chunk: Chunk
    dense_score: float | None = None
    bm25_score: float | None = None
    rrf_score: float | None = None
    rrf_rank: int | None = None
    rerank_score: float | None = None
