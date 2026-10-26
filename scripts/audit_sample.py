"""Draw a seeded random sample of `stated` fields from the second_pass records, as a checklist
for a hand audit in `make review`. Usage: audit_sample.py [n=35] [seed=4] [--sheet]

--sheet writes data/audit/audit_sheet.md instead: the same sample, each field with a page
excerpt around its quote, a pre-check line and an agree/disagree box for the auditor.

Only `stated` fields are sampled, so the result is a precision estimate for stated claims.
Write the outcome by hand to data/audit/second_pass_audit.json as
{"audited": N, "of": M, "disagreements": [{"slug", "field", "note"}]}."""

import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from extraction.extract import collect_sources  # noqa: E402

EXCERPT = 300  # characters of page text either side of the quote


def stated_fields(tier: str = "second_pass") -> list[tuple[str, str, dict]]:
    out = []
    s = get_settings()
    for f in sorted(s.resolve(s.paths.verified_dir).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("tier") != tier:
            continue
        for name, field in d["record"].items():
            if isinstance(field, dict) and field.get("status") == "stated":
                out.append((f.stem, name, field))
    return out


def excerpt(page: str, quote: str) -> str:
    page, quote = re.sub(r"\s+", " ", page), re.sub(r"\s+", " ", quote)
    i = page.find(quote)
    if i < 0:  # the quote check is word-normalised, so punctuation can differ; anchor on the first words
        i = page.find(" ".join(quote.split()[:6]))
    if i < 0:
        return "(quote not located verbatim; open it in make review)"
    return page[max(0, i - EXCERPT): i + len(quote) + EXCERPT]


def sheet(picks: list[tuple[str, str, dict]], of: int, seed: int) -> str:
    docs = {src.slug: src.docs for src in collect_sources(get_settings())}
    out = [f"# second_pass audit sheet\n\n{len(picks)} of {of} stated second_pass fields, seed {seed} "
           f"(`scripts/audit_sample.py {len(picks)} {seed} --sheet`).\n\n"
           "For each row: find the quote in the excerpt, check the value against it (digits, country lists, "
           "scope), then tick agree or write the disagreement.\n"]
    for i, (slug, name, f) in enumerate(picks, 1):
        out.append(f"## {i}. {slug} :: {name}\n\n"
                   f"- value: `{json.dumps(f['value'], ensure_ascii=False)}`\n"
                   f"- quote: \"{' '.join(f['quote'].split())}\"\n- doc: `{f['doc_id']}`\n"
                   f"- page excerpt:\n\n  > {excerpt(docs[slug].get(f['doc_id'], ''), f['quote'])}\n\n"
                   f"- pre-check: PENDING\n- auditor: [ ] agree  [ ] disagree: \n")
    return "\n".join(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--sheet"]
    n = int(args[0]) if args else 35
    seed = int(args[1]) if len(args) > 1 else 4
    pool = stated_fields()
    picks = sorted(random.Random(seed).sample(pool, min(n, len(pool))), key=lambda t: (t[0], t[1]))
    if "--sheet" in sys.argv:
        out = get_settings().resolve("data/audit/audit_sheet.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sheet(picks, len(pool), seed), encoding="utf-8")
        sys.exit(print(f"wrote {out}"))
    print(f"audit {len(picks)} of {len(pool)} stated second_pass fields (seed {seed})\n")
    for slug, name, f in picks:
        print(f"[ ] {slug} :: {name}\n    value: {json.dumps(f['value'], ensure_ascii=False)[:200]}\n    quote: {f['quote'][:200]}\n    doc:   {f['doc_id']}\n")
