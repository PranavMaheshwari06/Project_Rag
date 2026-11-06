"""Run ingestion: registry + raw cache -> data/processed/chunks.jsonl."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from core.logging import setup_logging
from ingestion.pipeline import THIN_DOC_WORDS, run_ingestion


def main():
    setup_logging()
    stats = run_ingestion(get_settings())
    print(f"ingested {stats['docs']} docs -> {stats['chunks']} chunks {stats['chunks_per_layer']}")
    for doc_id in stats["thin_docs"]:
        print(f"WARNING thin doc (<{THIN_DOC_WORDS} words after parsing, check it in data/raw/): {doc_id}")


if __name__ == "__main__":
    main()
