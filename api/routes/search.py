from fastapi import APIRouter, Depends, Request

from api.dependencies import get_retrieval_pipeline
from api.limits import limit_any
from api.middleware.logging_mw import trace
from core.metrics import StageTimer
from schemas.search import SearchRequest, SearchResponse

router = APIRouter(dependencies=[Depends(limit_any)])


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, request: Request) -> SearchResponse:
    pipeline = get_retrieval_pipeline()
    timer = StageTimer()
    results = pipeline.search(body.query, mode=body.mode, top_k=body.top_k, timer=timer,
                              filters=body.filters)
    trace(request, mode=body.mode, stages=timer.as_dict(), query_len=len(body.query))
    return SearchResponse(
        request_id=request.state.request_id,
        query=body.query,
        mode=body.mode,
        results=results,
        latency_ms=timer.as_dict(),
    )
