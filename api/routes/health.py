from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.config import get_settings

router = APIRouter()


@router.get("/health")
def health():
    """Liveness: the process answers. Never checks data, so a platform does not restart a container that is only not ready."""
    return {"status": "ok"}


@router.get("/ready")
def ready():
    """Readiness: 503 until the corpus and both indexes exist, so no traffic reaches an app that cannot answer."""
    settings = get_settings()
    index_dir = settings.resolve(settings.paths.index_dir)
    state = {
        "corpus_ingested": settings.resolve(settings.paths.processed_path).exists(),
        "bm25_index": (index_dir / "bm25.pkl").exists(),
        "dense_index": (index_dir / "dense.npz").exists() or settings.retrieval.vector_backend == "qdrant",
    }
    ok = all(state.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"ready": ok, **state, "vector_backend": settings.retrieval.vector_backend},
    )
