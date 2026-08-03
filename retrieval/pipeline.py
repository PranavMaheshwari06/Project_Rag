"""Orchestrates dense + BM25 + RRF + rerank and returns the full score trace
per chunk. Also owns index building so the script and the /ingest route share
one implementation."""

import logging

from core.config import Settings
from core.metrics import StageTimer
from ingestion.pipeline import load_chunks
from retrieval.bm25_index import BM25Index
from retrieval.embeddings import Embedder
from retrieval.hybrid import rrf_fuse
from retrieval.reranker import Reranker
from retrieval.vector_store import get_vector_store
from schemas.common import Chunk, RetrievedChunk

log = logging.getLogger(__name__)

MODES = ("vector", "bm25", "hybrid", "hybrid_rerank")


def build_indexes(settings: Settings) -> dict:
    chunks = load_chunks(settings)
    ids = [c.chunk_id for c in chunks]
    texts = [c.text for c in chunks]

    embedder = Embedder(settings.models.embed_model, settings.models.embed_batch_size)
    vectors = embedder.encode_passages(texts)

    dense = get_vector_store(settings)
    dense.build(ids, vectors)

    bm25 = BM25Index(settings.resolve(settings.paths.index_dir))
    bm25.build(ids, texts)

    log.info("indexed %d chunks (dense dim=%d, backend=%s)", len(ids), vectors.shape[1], settings.retrieval.vector_backend)
    return {"chunks": len(ids), "dim": int(vectors.shape[1])}


class RetrievalPipeline:
    def __init__(self, settings: Settings, embedder: Embedder, dense, bm25: BM25Index,
                 reranker: Reranker, chunks: dict[str, Chunk]):
        self.settings = settings
        self.embedder = embedder
        self.dense = dense
        self.bm25 = bm25
        self.reranker = reranker
        self.chunks = chunks

    def search(self, query: str, mode: str = "hybrid_rerank", top_k: int | None = None,
               timer: StageTimer | None = None) -> list[RetrievedChunk]:
        if mode not in MODES:
            raise ValueError(f"unknown retrieval mode: {mode}")
        timer = timer if timer is not None else StageTimer()
        cfg = self.settings.retrieval
        final_k = top_k or cfg.final_top_k

        dense_hits: list[tuple[str, float]] = []
        bm25_hits: list[tuple[str, float]] = []
        if mode != "bm25":
            with timer.track("dense_search"):
                qvec = self.embedder.encode_query(query)
                dense_hits = self.dense.search(qvec, cfg.dense_top_k)
        if mode != "vector":
            with timer.track("bm25_search"):
                bm25_hits = self.bm25.search(query, cfg.bm25_top_k)

        dense_scores = dict(dense_hits)
        bm25_scores = dict(bm25_hits)

        if mode == "vector":
            fused = [(cid, score) for cid, score in dense_hits]
        elif mode == "bm25":
            fused = [(cid, score) for cid, score in bm25_hits]
        else:
            with timer.track("rrf_fusion"):
                fused = rrf_fuse(
                    {"dense": [cid for cid, _ in dense_hits], "bm25": [cid for cid, _ in bm25_hits]},
                    k=cfg.rrf_k,
                )

        candidates: list[RetrievedChunk] = []
        for rank, (chunk_id, fused_score) in enumerate(fused, start=1):
            chunk = self.chunks.get(chunk_id)
            if chunk is None:
                continue  # stale index entry after a re-ingest
            candidates.append(RetrievedChunk(
                chunk=chunk,
                dense_score=dense_scores.get(chunk_id),
                bm25_score=bm25_scores.get(chunk_id),
                rrf_score=fused_score if mode in ("hybrid", "hybrid_rerank") else None,
                rrf_rank=rank if mode in ("hybrid", "hybrid_rerank") else None,
            ))

        if mode != "hybrid_rerank":
            return candidates[:final_k]

        pool = candidates[: cfg.rerank_n]
        with timer.track("rerank"):
            scores = self.reranker.score(query, [rc.chunk.text for rc in pool])
        for rc, score in zip(pool, scores):
            rc.rerank_score = score
        pool.sort(key=lambda rc: -(rc.rerank_score or 0.0))
        return pool[:final_k]


def build_pipeline(settings: Settings) -> RetrievalPipeline:
    chunks = {c.chunk_id: c for c in load_chunks(settings)}
    dense = get_vector_store(settings)
    dense.load()
    bm25 = BM25Index(settings.resolve(settings.paths.index_dir))
    bm25.load()
    embedder = Embedder(settings.models.embed_model, settings.models.embed_batch_size)
    reranker = Reranker(settings.models.rerank_model)
    return RetrievalPipeline(settings, embedder, dense, bm25, reranker, chunks)
