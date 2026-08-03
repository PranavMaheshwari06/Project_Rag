"""Cross-encoder reranker (bge-reranker-base, CPU). Scores are passed through
a sigmoid explicitly so the refusal threshold in settings.yaml is always
comparing against a stable 0..1 range, whatever the library's default
activation happens to be."""

import numpy as np


class Reranker:
    def __init__(self, model_name: str, batch_size: int = 8):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device="cpu", max_length=512)
        return self._model

    def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        model = self._load()
        logits = model.predict(
            [(query, t) for t in texts],
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        logits = np.asarray(logits, dtype=np.float64).reshape(-1)
        # some CrossEncoder versions already apply sigmoid; values in [0,1] pass through unchanged
        needs_sigmoid = logits.min() < 0 or logits.max() > 1
        probs = 1.0 / (1.0 + np.exp(-logits)) if needs_sigmoid else logits
        return [float(p) for p in probs]
