"""Extract a draft ProgramRequirements record per programme with the LLM and
write it to data/extracted/<slug>.json for review. Programmes that already
have a draft are skipped unless --refresh is passed (free-tier quota).
A failed programme keeps its previous draft; re-running retries only the missing ones.
Usage: make extract            (or: make extract ARGS="--refresh --only tum")"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from core.logging import setup_logging
from extraction.extract import FIELDS, collect_sources, extract_programme
from generation.llm_client import LLMClient


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-extract programmes that already have a draft")
    ap.add_argument("--only", default="", help="only programmes whose slug contains this text")
    args = ap.parse_args()

    setup_logging()
    settings = get_settings()
    llm = LLMClient(settings)
    if not llm.available:
        sys.exit("GEMINI_API_KEY is not set; extraction needs the LLM")

    out_dir = settings.resolve(settings.paths.extracted_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    called = False
    failed: list[str] = []
    for src in collect_sources(settings):
        out = out_dir / f"{src.slug}.json"
        if args.only not in src.slug or (out.exists() and not args.refresh):
            continue
        if called:
            time.sleep(settings.extraction.delay_seconds)
        called = True
        try:
            rec, rejected = extract_programme(src, llm, settings)
        except Exception as exc:  # provider overload, quota, invalid JSON twice: keep going
            failed.append(src.slug)
            print(f"{src.slug:<60} FAILED {type(exc).__name__}: {str(exc)[:120]}")
            continue
        out.write_text(json.dumps({
            "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": llm.model,
            "rejected_quotes": rejected,
            "record": rec.model_dump(mode="json"),
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        stated = sum(getattr(rec, f).status == "stated" for f in FIELDS)
        print(f"{src.slug:<60} stated {stated}/{len(FIELDS)}  rejected {len(rejected)}")
    if failed:
        sys.exit(f"{len(failed)} failed (previous drafts kept); re-run `make extract` to retry them")


if __name__ == "__main__":
    main()
