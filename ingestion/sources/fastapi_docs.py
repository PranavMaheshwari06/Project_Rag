"""FastAPI-style docs source. Reads the committed markdown sample from
data/samples/fastapi_docs so the pipeline runs fully offline. Swapping this for
a real crawler later only changes this file — the rest of the pipeline sees the
same RawDoc objects."""

from ingestion.crawler import RawDoc

BASE_URL = "https://docs.example.dev/fastapi"


def load(settings) -> list[RawDoc]:
    root = settings.resolve(settings.paths.sample_dir) / "fastapi_docs"
    docs = []
    for path in sorted(root.glob("*")):
        if path.suffix not in (".md", ".html"):
            continue
        docs.append(
            RawDoc(
                source="fastapi_docs",
                doc_id=f"fastapi_docs/{path.stem}",
                title_hint=path.stem.replace("-", " ").title(),
                url=f"{BASE_URL}/{path.stem}/",
                kind="markdown" if path.suffix == ".md" else "html",
                content=path.read_text(encoding="utf-8"),
            )
        )
    return docs
