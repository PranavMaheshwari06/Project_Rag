"""Fetch every registry source into data/raw/ and update sources/manifest.json.
Already-cached sources are skipped unless --refresh is passed.
Usage: make crawl            (or: make crawl ARGS="--refresh --only de/tum")"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from core.logging import setup_logging
from ingestion.crawler import crawl
from ingestion.registry import load_registry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-fetch sources that are already cached")
    ap.add_argument("--only", default="", help="only ids starting with this prefix")
    args = ap.parse_args()

    setup_logging()
    settings = get_settings()
    entries = [e for e in load_registry(settings.resolve(settings.paths.registry_path)) if e.id.startswith(args.only)]
    report = crawl(entries, settings, refresh=args.refresh)
    for row in report:
        extra = row.get("detail") or f"{row.get('type', '')} {row.get('bytes', '')}".strip()
        if row.get("redirected_to"):
            extra += f" -> {row['redirected_to']}"
        print(f"{row['result']:<18} {row['id']:<55} {extra}")
    print(dict(Counter(r["result"] for r in report)))


if __name__ == "__main__":
    main()
