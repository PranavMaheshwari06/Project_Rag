"""Loads raw documents from the registered sources. v1 is offline-only: every
source reads from the committed sample corpus. The max_docs bound is there so a
future live crawler can't silently balloon the corpus."""

from dataclasses import dataclass


@dataclass
class RawDoc:
    source: str
    doc_id: str
    title_hint: str
    url: str
    kind: str  # "html" | "markdown"
    content: str


def load_corpus(settings, max_docs: int = 200) -> list[RawDoc]:
    # imported here so sources can import RawDoc from this module without a cycle
    from ingestion.sources import extra_source, fastapi_docs

    docs: list[RawDoc] = []
    for loader in (fastapi_docs.load, extra_source.load):
        docs.extend(loader(settings))
    return docs[:max_docs]
