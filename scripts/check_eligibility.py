"""Check a profile against a programme's rules, or validate every rule file.
Offline: no LLM, no retrieval.

Usage: check_eligibility.py --profile p.json --programme <slug>
       check_eligibility.py --validate [--check-cache]   (exit 1 on any problem)"""

import argparse
import json
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from eligibility.engine import check_eligibility, default_groups  # noqa: E402
from eligibility.profile import Profile  # noqa: E402
from eligibility.rules import load_ruleset, uncited_quotes  # noqa: E402


def raw_page_words(settings, doc_id: str) -> str | None:
    """Plain text of the cached page, for quotes the parsed corpus lost (see LEARNING)."""
    from bs4 import BeautifulSoup
    from extraction.extract import _words

    manifest = json.loads(Path(settings.paths.manifest_path).read_text(encoding="utf-8"))
    rec = manifest.get(doc_id)
    path = Path(settings.paths.raw_dir) / rec["file"] if rec and rec.get("file") else None
    if not path or not path.is_file():
        return None
    return _words(BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").get_text(" "))


def validate(settings, check_cache: bool = False) -> list[str]:
    """Quotes must be inside a verified-record quote (checked everywhere) or, for
    evidence the record omits, inside the cached raw page (checked only where
    data/raw exists, so CI cannot claim page verification). `check_cache` makes
    a missing cached page an error, for the local run where data/raw exists."""
    from extraction.extract import _words

    errors = []
    for path in sorted(Path(settings.paths.rules_dir).glob("*.json")):
        rules, stale = load_ruleset(settings, path.stem)
        if stale:
            errors.append(f"{path.stem}: stale, the verified record changed")
        record = json.loads((Path(settings.paths.verified_dir) / path.name).read_text(encoding="utf-8"))["record"]
        for rule_id, doc_id, quote in uncited_quotes(rules, record):
            page = raw_page_words(settings, doc_id)
            if page is None and check_cache:
                errors.append(f"{path.stem}: {rule_id}: quote not in record, cached page unavailable")
            elif page is None:
                print(f"{path.stem}: {rule_id}: quote not in record, cached page unavailable, not checked")
            elif _words(quote) not in page:
                errors.append(f"{path.stem}: {rule_id}: quote not in record or cached page: {quote[:60]!r}")
    for name, g in default_groups().groups.items():
        if date.today() > g.recheck_after:
            errors.append(f"country list {name} is past its re-check date {g.recheck_after}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--programme")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--check-cache", action="store_true", help="with --validate: a missing cached page is an error")
    args = ap.parse_args()
    settings = get_settings()
    if args.validate:
        errors = validate(settings, args.check_cache)
        print("\n".join(errors) or f"{len(list(Path(settings.paths.rules_dir).glob('*.json')))} rule files OK")
        return 1 if errors else 0
    if not (args.profile and args.programme):
        ap.error("--profile and --programme are required unless --validate")
    profile = Profile.model_validate_json(Path(args.profile).read_text(encoding="utf-8"))
    report = check_eligibility(profile, *load_ruleset(settings, args.programme), as_of=date.today())
    print(f"{report.slug}: {report.headline}{' (rules stale)' if report.rules_stale else ''}")
    for c in report.criteria:
        margin = f" margin {c.margin}" if c.margin is not None else ""
        print(f"  [{c.verdict}] {c.label}{margin}" + (f"\n      -> {c.action}" if c.action else ""))
    for n in report.notices:
        print(f"  notice: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
