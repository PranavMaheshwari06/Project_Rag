from fastapi import APIRouter, Request

from api.dependencies import get_retrieval_pipeline
from core.metrics import StageTimer
from schemas.search import SearchRequest, SearchResponse

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, request: Request) -> SearchResponse:
    pipeline = get_retrieval_pipeline()
    timer = StageTimer()
    results = pipeline.search(body.query, mode=body.mode, top_k=body.top_k, timer=timer)
    return SearchResponse(
        request_id=request.state.request_id,
        query=body.query,
        mode=body.mode,
        results=results,
        latency_ms=timer.as_dict(),
    )
