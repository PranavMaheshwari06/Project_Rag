from fastapi import APIRouter

from core.config import get_settings

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "corpus_ingested": settings.resolve(settings.paths.processed_path).exists(),
        "bm25_index": (settings.resolve(settings.paths.index_dir) / "bm25.pkl").exists(),
        "dense_index": (settings.resolve(settings.paths.index_dir) / "dense.npz").exists()
        or settings.retrieval.vector_backend == "qdrant",
        "vector_backend": settings.retrieval.vector_backend,
    }
