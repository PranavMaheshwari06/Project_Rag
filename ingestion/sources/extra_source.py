"""Second source so the pipeline provably handles more than one corpus. Reads
data/samples/extra (currently one HTML ops guide, which also exercises the HTML
parser and boilerplate cleaner)."""

from ingestion.crawler import RawDoc

BASE_URL = "https://wiki.example.dev/ops"


def load(settings) -> list[RawDoc]:
    root = settings.resolve(settings.paths.sample_dir) / "extra"
    docs = []
    for path in sorted(root.glob("*")):
        if path.suffix not in (".md", ".html"):
            continue
        docs.append(
            RawDoc(
                source="ops_notes",
                doc_id=f"ops_notes/{path.stem}",
                title_hint=path.stem.replace("-", " ").title(),
                url=f"{BASE_URL}/{path.stem}/",
                kind="markdown" if path.suffix == ".md" else "html",
                content=path.read_text(encoding="utf-8"),
            )
        )
    return docs
