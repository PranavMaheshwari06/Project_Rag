"""Dense embeddings via bge-small on CPU. The sentence-transformers import is
deferred so modules that only need pure logic (chunker, RRF, tests) never pull
in torch."""

import numpy as np

# bge models want this prefix on queries but not on passages
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class Embedder:
    def __init__(self, model_name: str, batch_size: int = 16):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.astype(np.float32)

    def count_truncated(self, texts: list[str]) -> int:
        """Passages longer than the model's max_seq_length are silently cut;
        their tail is invisible to dense retrieval."""
        model = self._load()
        lengths = [len(ids) for ids in model.tokenizer(texts, add_special_tokens=True)["input_ids"]]
        return sum(n > model.max_seq_length for n in lengths)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode_passages([QUERY_PREFIX + text])[0]
