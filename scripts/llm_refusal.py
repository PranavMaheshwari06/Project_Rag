"""End-to-end refusal rate of one-shot RAG with the LLM on, on every gold item except
the multi-hop ones (those are the agent comparison's). Needs GEMINI_API_KEY and the
local indexes. Appends one row per item to evaluation/results/llm_refusal.jsonl and
stops cleanly when the quota runs out; run it again to resume. Writes the summary
to evaluation/results/llm_refusal.json.

  make eval-llm-refusal                        # run what is missing, then summarise
  make eval-llm-refusal ARGS="--limit 10"      # at most 10 items this run
  make eval-llm-refusal ARGS="--summary-only"  # no LLM calls"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from core.logging import setup_logging  # noqa: E402
from evaluation.agent_eval import load_rows  # noqa: E402
from evaluation.llm_refusal_eval import run_items, summarize  # noqa: E402
from evaluation.retrieval_eval import load_gold  # noqa: E402
from generation.llm_client import LLMClient  # noqa: E402


def positive(text: str) -> int:
    n = int(text)
    if n < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=positive, default=None, help="items to run this time")
    ap.add_argument("--delay", type=float, default=6.0, help="seconds between LLM calls (per-minute limit)")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    settings = get_settings()
    items = [i for i in load_gold(settings.resolve(settings.evaluation.gold_path)) if i.kind != "multi_hop"]
    rows_path = settings.resolve(settings.evaluation.llm_refusal_rows_out)
    status = 0
    if not args.summary_only:
        llm = LLMClient(settings)
        if not llm.available:
            print("GEMINI_API_KEY is not set; nothing run (use --summary-only to summarise).")
            return 1
        from retrieval.pipeline import build_pipeline  # loads the models: only when running

        written, stopped = run_items(items, settings, build_pipeline(settings), llm, rows_path,
                                     limit=args.limit, delay_s=args.delay)
        print(f"{written} new rows in {rows_path.name}")
        if stopped:
            print(f"stopped at {stopped}; run again later to resume")
            status = 2
    summary = summarize(load_rows(rows_path), settings.evaluation.bootstrap_resamples,
                        settings.evaluation.bootstrap_seed)
    settings.resolve(settings.evaluation.llm_refusal_out).write_text(json.dumps(summary, indent=2) + "\n",
                                                                     encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
