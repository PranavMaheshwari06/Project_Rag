"""Check a profile against a programme's rules, or validate every rule file.
Offline: no LLM, no retrieval.

Usage: check_eligibility.py --profile p.json --programme <slug>
       check_eligibility.py --validate     (exit 1 on any problem)"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from eligibility.engine import check_eligibility  # noqa: E402
from eligibility.profile import Profile  # noqa: E402
from eligibility.rules import load_ruleset, uncited_quotes  # noqa: E402


def validate(settings) -> list[str]:
    errors = []
    for path in sorted(Path(settings.paths.rules_dir).glob("*.json")):
        rules, stale = load_ruleset(settings, path.stem)
        if stale:
            errors.append(f"{path.stem}: stale, the verified record changed")
        record = json.loads((Path(settings.paths.verified_dir) / path.name).read_text(encoding="utf-8"))["record"]
        errors += [f"{path.stem}: quote not in record: {e}" for e in uncited_quotes(rules, record)]
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--programme")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    settings = get_settings()
    if args.validate:
        errors = validate(settings)
        print("\n".join(errors) or f"{len(list(Path(settings.paths.rules_dir).glob('*.json')))} rule files OK")
        return 1 if errors else 0
    if not (args.profile and args.programme):
        ap.error("--profile and --programme are required unless --validate")
    profile = Profile.model_validate_json(Path(args.profile).read_text(encoding="utf-8"))
    report = check_eligibility(profile, *load_ruleset(settings, args.programme))
    print(f"{report.slug}: {report.headline}{' (rules stale)' if report.rules_stale else ''}")
    for c in report.criteria:
        margin = f" margin {c.margin}" if c.margin is not None else ""
        print(f"  [{c.verdict}] {c.label}{margin}" + (f"\n      -> {c.action}" if c.action else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
