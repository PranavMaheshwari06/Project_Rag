"""Validate the eligibility cases, run them through the engine and write the
metrics (plan section 7). Offline: no LLM, no retrieval.

Usage: eval_eligibility.py [--cases file.jsonl] [--out results.json]
Exit 1 if the dataset is missing or invalid; nothing is written then."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from evaluation.eligibility_dataset import load_cases, validate_cases  # noqa: E402
from evaluation.eligibility_eval import run_cases, write_results  # noqa: E402


def main(argv: list[str] | None = None, settings=None) -> int:
    settings = settings or get_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=settings.evaluation.eligibility_cases_path)
    ap.add_argument("--out", default=settings.evaluation.eligibility_results_out)
    args = ap.parse_args(argv)
    cases_path = Path(args.cases)
    if not cases_path.is_file():
        print(f"no eligibility dataset at {cases_path}; nothing evaluated")
        return 1
    try:
        cases = load_cases(cases_path)
    except ValueError as e:
        print(e)
        return 1
    problems = validate_cases(cases, settings)
    if problems:
        print("\n".join(problems))
        return 1
    results = run_cases(cases, settings, dataset_path=cases_path)
    write_results(results, Path(args.out))
    m = results["metrics"]
    print(f"{m['cases']} cases -> {args.out}")
    print(f"  headline agreement {m['headline_agreement']['agree']}/{m['headline_agreement']['total']}, "
          f"criterion agreement {m['criterion_agreement']['agree']}/{m['criterion_agreement']['total']}, "
          f"false-positive headlines {m['false_positive_headlines']}")
    for author, sub in m["by_author"].items():
        print(f"  {author}: {sub['cases']} cases, headline agreement {sub['headline_agreement']['agree']}/{sub['cases']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
