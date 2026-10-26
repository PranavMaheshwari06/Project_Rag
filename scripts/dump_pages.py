"""Write each programme's cleaned page text to data/pages/<slug>/ so a
cross-checker reads exactly the text the quote check uses.
Usage: .venv/bin/python scripts/dump_pages.py [slug-filter]"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from extraction.extract import collect_sources


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    settings = get_settings()
    for src in collect_sources(settings):
        if only not in src.slug:
            continue
        out = settings.resolve("data/pages") / src.slug
        out.mkdir(parents=True, exist_ok=True)
        index = {}
        for i, (doc_id, text) in enumerate(src.docs.items(), 1):
            name = f"{i}.txt"
            (out / name).write_text(text, encoding="utf-8")
            index[doc_id] = name
        (out / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        print(f"{src.slug}: {len(index)} pages")


if __name__ == "__main__":
    main()
