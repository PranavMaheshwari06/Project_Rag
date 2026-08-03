"""Run ingestion: sample corpus -> data/processed/chunks.jsonl."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from core.logging import setup_logging
from ingestion.pipeline import run_ingestion


def main():
    setup_logging()
    stats = run_ingestion(get_settings())
    print(f"ingested {stats['docs']} docs -> {stats['chunks']} chunks")


if __name__ == "__main__":
    main()
