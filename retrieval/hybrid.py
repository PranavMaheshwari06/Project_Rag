"""Reciprocal Rank Fusion. Rank-based, so dense cosine and BM25 scores never
have to share a scale — which is exactly why RRF over a weighted score sum
here (see DECISIONS.md)."""


def rrf_fuse(rankings: dict[str, list[str]], k: int = 60) -> list[tuple[str, float]]:
    """rankings maps a retriever name to its result ids, best first.
    Returns (id, fused_score) best first. Ties break lexically on id so the
    output is deterministic across runs."""
    scores: dict[str, float] = {}
    for ids in rankings.values():
        for rank, chunk_id in enumerate(ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
