"""End-to-end ingestion: crawl -> parse -> clean -> chunk -> chunks.jsonl."""

import logging

from core.config import Settings
from core.exceptions import CorpusNotIngestedError
from ingestion.chunker import chunk_document
from ingestion.cleaner import clean
from ingestion.crawler import load_corpus
from ingestion.parser import parse
from schemas.common import Chunk

log = logging.getLogger(__name__)


def run_ingestion(settings: Settings) -> dict:
    raw_docs = load_corpus(settings)
    chunks: list[Chunk] = []
    for raw in raw_docs:
        parsed = parse(raw)
        parsed.text = clean(parsed.text)
        chunks.extend(chunk_document(parsed, settings.chunking))

    out_path = settings.resolve(settings.paths.processed_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for chunk in chunks:
            fh.write(chunk.model_dump_json() + "\n")

    log.info("ingested %d docs into %d chunks -> %s", len(raw_docs), len(chunks), out_path)
    return {"docs": len(raw_docs), "chunks": len(chunks)}


def load_chunks(settings: Settings) -> list[Chunk]:
    path = settings.resolve(settings.paths.processed_path)
    if not path.exists():
        raise CorpusNotIngestedError()
    with path.open(encoding="utf-8") as fh:
        return [Chunk.model_validate_json(line) for line in fh if line.strip()]
