"""Check the gold set against the registry and the current chunks before any eval run.
Exits 1 on any problem. Usage: validate_gold.py [gold.jsonl]"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from evaluation.retrieval_eval import KINDS, GoldItem, load_gold  # noqa: E402
from extraction.review import _numbers  # noqa: E402
from ingestion.registry import load_registry  # noqa: E402

NO_DOCS = {"refusal", "coverage"}
WHO = {"model", "human"}


def validate(items: list[GoldItem], registry_ids: set[str], sections: dict[str, set[str]],
             texts: dict[str, str]) -> list[str]:
    errors, seen = [], set()
    for g in items:
        err = lambda msg: errors.append(f"{g.qid}: {msg}")  # noqa: E731
        if g.qid in seen:
            err("duplicate qid")
        seen.add(g.qid)
        if g.kind not in KINDS:
            err(f"kind {g.kind!r} not in {sorted(KINDS)}")
        if g.author not in WHO or g.reviewed_by not in WHO:
            err("author and reviewed_by must be model or human")
        if g.kind in NO_DOCS:
            if g.relevant_doc_ids:
                err(f"{g.kind} item must have no doc ids")
            continue
        if not g.relevant_doc_ids:
            err("no doc ids")
        for d in g.relevant_doc_ids:
            if d not in registry_ids:
                err(f"doc {d} not in registry")
            elif d not in texts:
                err(f"doc {d} has no chunks (run make ingest)")
        for s in g.relevant_sections:
            if not any(s.lower() in p.lower() for d in g.relevant_doc_ids for p in sections.get(d, ())):
                err(f"section {s!r} matches no section_path of its docs")
        text = " ".join(texts.get(d, "") for d in g.relevant_doc_ids)
        missing = _numbers(g.answer_hint) - _numbers(text)
        if missing:
            err(f"hint numbers not in doc text: {sorted(missing)}")
        for e in g.evidence:
            if e.get("doc_id") not in g.relevant_doc_ids:
                err(f"evidence doc {e.get('doc_id')} is not a relevant doc")
            elif " ".join(str(e.get("quote", "")).split()) not in " ".join(texts.get(e["doc_id"], "").split()):
                err(f"evidence quote not in {e['doc_id']}: {str(e.get('quote'))[:60]!r}")
    return errors


def main():
    s = get_settings()
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else s.resolve(s.evaluation.gold_path)
    sections, texts = defaultdict(set), defaultdict(str)
    with s.resolve(s.paths.processed_path).open(encoding="utf-8") as fh:
        for line in fh:
            c = json.loads(line)
            sections[c["doc_id"]].add(c["section_path"])
            texts[c["doc_id"]] += " " + c["text"]
    items = load_gold(path)
    errors = validate(items, {e.id for e in load_registry(s.resolve(s.paths.registry_path))}, sections, texts)
    print("\n".join(errors) or f"{path.name}: {len(items)} items ok")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
