"""Run the 4-way retrieval benchmark and write frontend/public/benchmark.json
plus the README table. First run downloads the reranker model (~1.1GB)."""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import DEFAULT_CONFIG, get_settings
from core.logging import setup_logging
from evaluation.runner import render_markdown_table, run_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-threshold", action="store_true", help="persist the calibrated refusal threshold")
    args = parser.parse_args()
    setup_logging()
    result = run_benchmark(get_settings())
    if args.apply_threshold:
        calibration = result.refusal_calibration
        if calibration["status"] != "calibrated" or not calibration["constraint_met"]:
            raise SystemExit("Calibration did not meet the constraint; configuration was not changed.")
        value = repr(calibration["selected_threshold"])
        content = DEFAULT_CONFIG.read_text(encoding="utf-8")
        content, replacements = re.subn(r"(?m)^(  refusal_threshold:) [^\n]+$",
                                       lambda m: f"{m[1]} {value}  # calibrated; see evaluation/results/", content)
        if replacements != 1:
            raise SystemExit("Could not locate exactly one refusal_threshold setting.")
        DEFAULT_CONFIG.write_text(content, encoding="utf-8")
    print()
    print(render_markdown_table(result))


if __name__ == "__main__":
    main()
