"""Run the 4-way retrieval benchmark and write frontend/public/benchmark.json
plus the README table. First run downloads the reranker model (~1.1GB)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings
from core.logging import setup_logging
from evaluation.runner import render_markdown_table, run_benchmark


def main():
    setup_logging()
    result = run_benchmark(get_settings())
    print()
    print(render_markdown_table(result))


if __name__ == "__main__":
    main()
