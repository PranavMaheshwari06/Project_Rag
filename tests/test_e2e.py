"""End-to-end: real ingestion -> real indexes -> grounded answer with working
citations, and an explicit refusal for a question the corpus can't answer."""

from generation.prompt_builder import REFUSAL_TEXT


def test_grounded_answer_with_citations(client):
    resp = client.post("/answer", json={"query": "How do I run work after the response has been sent?"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["refused"] is False
    assert body["answer"] != REFUSAL_TEXT
    assert body["citations"], "grounded answer must cite its evidence"

    # every citation must resolve to a chunk that was actually retrieved
    retrieved_ids = {rc["chunk"]["chunk_id"] for rc in body["chunks"]}
    for citation in body["citations"]:
        assert citation["chunk_id"] in retrieved_ids
        assert f"[{citation['marker']}]" in body["answer"]
        assert citation["url"].startswith("https://")

    # the score trace is present end to end
    top = body["chunks"][0]
    assert top["rerank_score"] is not None
    assert top["rrf_rank"] is not None


def test_refuses_out_of_corpus_question(client):
    resp = client.post("/answer", json={"query": "Who won the 2010 FIFA World Cup final?"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["refused"] is True
    assert body["answer"] == REFUSAL_TEXT
    assert body["citations"] == []
    assert body["mode"] == "refusal"


def test_search_trace_scores_consistent(client):
    resp = client.post("/search", json={"query": "database session dependency", "mode": "hybrid_rerank"})
    body = resp.json()
    results = body["results"]
    assert results
    # sorted by rerank score, each fused hit has at least one retriever score
    rerank_scores = [r["rerank_score"] for r in results]
    assert rerank_scores == sorted(rerank_scores, reverse=True)
    for r in results:
        assert r["dense_score"] is not None or r["bm25_score"] is not None
