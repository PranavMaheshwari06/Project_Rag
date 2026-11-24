from fastapi import APIRouter, Depends, Request

from api.dependencies import require_admin, reset_pipeline
from core.config import get_settings
from core.metrics import StageTimer
from ingestion.pipeline import run_ingestion
from retrieval.pipeline import build_indexes
from schemas.ingest import IngestRequest, IngestResponse

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/ingest", response_model=IngestResponse)
def ingest(body: IngestRequest, request: Request) -> IngestResponse:
    settings = get_settings()
    timer = StageTimer()

    with timer.track("ingestion"):
        stats = run_ingestion(settings)
    if body.rebuild_indexes:
        with timer.track("indexing"):
            build_indexes(settings)
        reset_pipeline()
        request.app.state.answer_cache.clear()  # cached answers came from the old indexes

    return IngestResponse(
        request_id=request.state.request_id,
        docs=stats["docs"],
        chunks=stats["chunks"],
        indexes_rebuilt=body.rebuild_indexes,
        latency_ms=timer.as_dict(),
    )
