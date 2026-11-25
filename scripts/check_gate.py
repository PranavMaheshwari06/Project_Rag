"""CI eval gate: the eligibility cases run here, and the committed eval results are checked against the bounds in
evaluation/gate_floors.json. Offline: no LLM, no retrieval, nothing written.

It re-runs neither retrieval nor the LLM (the corpus is not committed), so it catches a worse or outdated committed
result, not a code change that nobody re-evaluated.

Usage: check_gate.py [--floors file.json]. Exit 1 if any check fails."""

import argparse
import hashlib
import json
import sys
from functools import reduce
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import Settings, get_settings  # noqa: E402
from evaluation.eligibility_dataset import load_cases, validate_cases  # noqa: E402
from evaluation.eligibility_eval import run_cases  # noqa: E402

FLOORS = "evaluation/gate_floors.json"
LIVE = "live:eligibility"  # the one source that is computed here instead of read from a file


def _number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _sha256_is(v, path: Path) -> bool:
    return path.is_file() and v == hashlib.sha256(path.read_bytes()).hexdigest()


OPS = {
    "min": lambda v, bound, settings: _number(v) and v >= bound,
    "max": lambda v, bound, settings: _number(v) and v <= bound,
    "equals": lambda v, bound, settings: v == bound,
    "equals_setting": lambda v, bound, settings: v == reduce(getattr, bound.split("."), settings),
    "sha256_of": lambda v, bound, settings: _sha256_is(v, settings.resolve(bound)),
}


def lookup(doc, path: str):
    """`a.b.0.c`; in a list, a part that is not a number picks the item with that `name`."""
    for part in path.split("."):
        if isinstance(doc, list):
            doc = doc[int(part)] if part.isdigit() else next(x for x in doc if x["name"] == part)
        else:
            doc = doc[part]
    return doc


def failures(doc, rules: dict, source: str, settings: Settings) -> list[str]:
    """One line per check that does not hold. A missing value, an empty rule and an unknown check all fail."""
    out = []
    for path, rule in rules.items():
        try:
            value = lookup(doc, path)
        except (KeyError, IndexError, StopIteration, TypeError):
            out.append(f"{source}: {path} is missing")
            continue
        if not rule or rule.keys() - OPS.keys():
            out.append(f"{source}: {path} has no check or an unknown one: {rule}")
            continue
        out += [f"{source}: {path} = {value}, required {op} {bound}"
                for op, bound in rule.items() if not OPS[op](value, bound, settings)]
    return out


def live_eligibility(settings: Settings) -> dict:
    path = settings.resolve(settings.evaluation.eligibility_cases_path)
    cases = load_cases(path)
    if problems := validate_cases(cases, settings):
        raise ValueError("invalid eligibility cases:\n" + "\n".join(problems))
    return run_cases(cases, settings, dataset_path=path)


def run(settings: Settings, floors_path: Path) -> tuple[list[str], int]:
    """(failed checks, number of checks listed)."""
    failed, checked = [], 0
    for source, rules in json.loads(floors_path.read_text(encoding="utf-8")).items():
        if source.startswith("_"):
            continue
        checked += len(rules)
        if not rules:
            failed.append(f"{source}: no checks listed")
            continue
        try:
            doc = (live_eligibility(settings) if source == LIVE
                   else json.loads(settings.resolve(source).read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            failed.append(f"{source}: cannot be read: {e}")
            continue
        failed += failures(doc, rules, source, settings)
    if not checked:
        failed.append(f"{floors_path.name}: holds no checks")
    return failed, checked


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    ap = argparse.ArgumentParser(description="Check the eval results against the committed floors.")
    ap.add_argument("--floors", default=settings.resolve(FLOORS))
    args = ap.parse_args(argv)
    failed, checked = run(settings, Path(args.floors))
    for line in failed:
        print(f"FAIL {line}")
    print(f"eval gate: {checked} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
