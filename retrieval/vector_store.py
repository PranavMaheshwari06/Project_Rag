"""Two dense-index backends behind one interface: a NumPy brute-force store for
local runs, and a Qdrant-backed store for the containerized phase. Both return
(chunk_id, cosine_score) pairs; vectors arrive L2-normalized so a dot product
is cosine similarity."""

import uuid
from pathlib import Path

import numpy as np

from core.config import Settings
from core.exceptions import IndexNotBuiltError

DenseHits = list[tuple[str, float]]


class MemoryVectorStore:
    """Brute-force cosine over an in-memory matrix, persisted as .npz.
    Plenty fast for a few thousand chunks; swap the backend in settings.yaml
    when the corpus outgrows it."""

    def __init__(self, index_dir: Path):
        self.path = index_dir / "dense.npz"
        self._ids: list[str] = []
        self._matrix: np.ndarray | None = None

    def build(self, ids: list[str], vectors: np.ndarray) -> None:
        self._ids = list(ids)
        self._matrix = np.asarray(vectors, dtype=np.float32)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(self.path, ids=np.array(self._ids), vectors=self._matrix)

    def load(self) -> None:
        if not self.path.exists():
            raise IndexNotBuiltError()
        data = np.load(self.path, allow_pickle=False)
        self._ids = [str(x) for x in data["ids"]]
        self._matrix = data["vectors"]

    def search(self, vector: np.ndarray, top_k: int) -> DenseHits:
        if self._matrix is None:
            raise IndexNotBuiltError()
        sims = self._matrix @ vector
        order = np.argsort(-sims)[:top_k]
        return [(self._ids[i], float(sims[i])) for i in order]


class QdrantVectorStore:
    """Same interface against a Qdrant collection. Used in the containerized
    phase (docker-compose); also works against any reachable Qdrant instance.
    Point ids are uuid5 of the chunk_id, the chunk_id itself rides in the payload."""

    def __init__(self, url: str, collection: str):
        self.url = url
        self.collection = collection
        self._client = None

    def _connect(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.url)
        return self._client

    def build(self, ids: list[str], vectors: np.ndarray) -> None:
        from qdrant_client.models import Distance, PointStruct, VectorParams

        client = self._connect()
        dim = int(vectors.shape[1])
        client.recreate_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)),
                vector=vectors[i].tolist(),
                payload={"chunk_id": chunk_id},
            )
            for i, chunk_id in enumerate(ids)
        ]
        client.upsert(collection_name=self.collection, points=points)

    def load(self) -> None:
        client = self._connect()
        if not client.collection_exists(self.collection):
            raise IndexNotBuiltError(f"Qdrant collection '{self.collection}' does not exist yet.")

    def search(self, vector: np.ndarray, top_k: int) -> DenseHits:
        client = self._connect()
        hits = client.query_points(
            collection_name=self.collection, query=vector.tolist(), limit=top_k, with_payload=True
        ).points
        return [(h.payload["chunk_id"], float(h.score)) for h in hits]


def get_vector_store(settings: Settings):
    if settings.retrieval.vector_backend == "qdrant":
        return QdrantVectorStore(settings.retrieval.qdrant_url, settings.retrieval.collection)
    return MemoryVectorStore(settings.resolve(settings.paths.index_dir))
