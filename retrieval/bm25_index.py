"""In-process BM25 over a code-aware tokenizer, persisted with pickle. The
tokenizer keeps the original identifier AND its snake_case/camelCase parts, so
a query for "background tasks" matches `BackgroundTasks` in code blocks."""

import pickle
import re
from pathlib import Path

from core.exceptions import IndexNotBuiltError

WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")
CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in WORD_RE.findall(text):
        lowered = raw.lower()
        tokens.append(lowered)
        parts = [p for piece in raw.split("_") for p in CAMEL_RE.split(piece) if p]
        if len(parts) > 1:
            tokens.extend(p.lower() for p in parts)
    return tokens


class BM25Index:
    def __init__(self, index_dir: Path):
        self.path = index_dir / "bm25.pkl"
        self._bm25 = None
        self._ids: list[str] = []

    def build(self, ids: list[str], texts: list[str]) -> None:
        from rank_bm25 import BM25Okapi

        corpus = [tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(corpus)
        self._ids = list(ids)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("wb") as fh:
            pickle.dump({"ids": self._ids, "bm25": self._bm25}, fh)

    def load(self) -> None:
        if not self.path.exists():
            raise IndexNotBuiltError()
        with self.path.open("rb") as fh:
            data = pickle.load(fh)
        self._ids = data["ids"]
        self._bm25 = data["bm25"]

    def search(self, query: str, top_k: int) -> list[tuple[str, float]]:
        if self._bm25 is None:
            raise IndexNotBuiltError()
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        return [(self._ids[i], float(scores[i])) for i in order if scores[i] > 0]
