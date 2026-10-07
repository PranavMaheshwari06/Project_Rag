"""Build the dense + BM25 indexes from chunks.jsonl. First run downloads the
embedding model (~130MB), so give it a minute."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from core.logging import setup_logging
from retrieval.pipeline import build_indexes


def main():
    setup_logging()
    stats = build_indexes(get_settings())
    print(f"indexed {stats['chunks']} chunks (dense dim={stats['dim']}, {stats['truncated']} truncated at the embedder's token limit)")


if __name__ == "__main__":
    main()
