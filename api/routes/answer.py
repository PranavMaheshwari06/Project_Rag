from collections.abc import Iterator

from fastapi import APIRouter, Depends, Request

from api.cache import TTLCache, answer_key
from api.dependencies import get_llm_client, get_retrieval_pipeline
from api.limits import limit_llm
from api.middleware.logging_mw import trace
from core.config import get_settings
from core.metrics import StageTimer
from generation.answer_generator import generate_answer
from generation.citation_mapper import map_citations
from schemas.answer import AnswerRequest, AnswerResponse
from schemas.common import RetrievedChunk

NOT_CACHED = {"uncited", "guardrail"}  # contract failures: a retry can succeed

router = APIRouter(dependencies=[Depends(limit_llm)])


def answer_steps(query: str, filters: dict | None, request_id: str,
                 cache: TTLCache | None) -> Iterator[list[RetrievedChunk] | AnswerResponse]:
    """One-shot RAG through the response cache (None = do not cache). Yields the retrieved passages as soon as
    they are known, then the response, so /chat/stream can show them while the model is still working."""
    key = answer_key(query, filters)
    if cache is not None and (hit := cache.get(key)) is not None:
        response = hit.model_copy(deep=True, update={"request_id": request_id, "query": query, "cached": True,
                                                     "latency_ms": {}})
        yield response.chunks
        yield response
        return

    gen = cache.gen if cache is not None else None  # read before retrieval: a rebuild from here on makes it stale
    settings = get_settings()
    timer = StageTimer()
    retrieved = get_retrieval_pipeline().search(query, mode="hybrid_rerank", timer=timer, filters=filters)
    yield retrieved
    with timer.track("generation"):
        draft = generate_answer(query, retrieved, settings, get_llm_client())
        text, citations = map_citations(draft.text, draft.evidence)

    response = AnswerResponse(
        request_id=request_id,
        query=query,
        answer=text,
        refused=draft.refused,
        mode=draft.mode,
        refusal_reason=draft.refusal_reason,
        citations=citations,
        chunks=retrieved,
        latency_ms=timer.as_dict(),
    )
    # errors raise before this line
    if cache is not None and draft.refusal_reason not in NOT_CACHED:
        cache.put(key, response.model_copy(deep=True, update={"query": ""}), gen)
    yield response


@router.post("/answer", response_model=AnswerResponse)
def answer(body: AnswerRequest, request: Request) -> AnswerResponse:
    *_, response = answer_steps(body.query, body.filters, request.state.request_id, request.app.state.answer_cache)
    trace(request, cached=response.cached, mode=response.mode, refused=response.refused,
          refusal_reason=response.refusal_reason, stages=response.latency_ms, query_len=len(body.query))
    return response
