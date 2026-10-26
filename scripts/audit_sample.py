"""Draw a seeded random sample of `stated` fields from the second_pass records, as a checklist
for a hand audit in `make review`. Usage: audit_sample.py [n=35] [seed=4]

Only `stated` fields are sampled, so the result is a precision estimate for stated claims.
Write the outcome by hand to data/audit/second_pass_audit.json as
{"audited": N, "of": M, "disagreements": [{"slug", "field", "note"}]}."""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402


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


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    pool = stated_fields()
    picks = sorted(random.Random(seed).sample(pool, min(n, len(pool))), key=lambda t: (t[0], t[1]))
    print(f"audit {len(picks)} of {len(pool)} stated second_pass fields (seed {seed})\n")
    for slug, name, f in picks:
        print(f"[ ] {slug} :: {name}\n    value: {json.dumps(f['value'], ensure_ascii=False)[:200]}\n    quote: {f['quote'][:200]}\n    doc:   {f['doc_id']}\n")
