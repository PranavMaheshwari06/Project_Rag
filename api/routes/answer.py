from fastapi import APIRouter, Depends, Request

from api.dependencies import get_llm_client, get_retrieval_pipeline
from api.limits import limit_llm
from api.middleware.logging_mw import trace
from core.config import get_settings
from core.metrics import StageTimer
from generation.answer_generator import generate_answer
from generation.citation_mapper import map_citations
from schemas.answer import AnswerRequest, AnswerResponse

router = APIRouter(dependencies=[Depends(limit_llm)])


@router.post("/answer", response_model=AnswerResponse)
def answer(body: AnswerRequest, request: Request) -> AnswerResponse:
    settings = get_settings()
    pipeline = get_retrieval_pipeline()
    timer = StageTimer()

    retrieved = pipeline.search(body.query, mode="hybrid_rerank", timer=timer, filters=body.filters)
    with timer.track("generation"):
        draft = generate_answer(body.query, retrieved, settings, get_llm_client())
        text, citations = map_citations(draft.text, draft.evidence)

    trace(request, mode=draft.mode, refused=draft.refused, refusal_reason=draft.refusal_reason,
          stages=timer.as_dict(), query_len=len(body.query))
    return AnswerResponse(
        request_id=request.state.request_id,
        query=body.query,
        answer=text,
        refused=draft.refused,
        mode=draft.mode,
        refusal_reason=draft.refusal_reason,
        citations=citations,
        chunks=retrieved,
        latency_ms=timer.as_dict(),
    )
