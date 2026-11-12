"""Phase 7 comparison: agent vs one-shot RAG on the human-reviewed multi_hop gold
items. Needs GEMINI_API_KEY and the local indexes (make ingest && make index).
Appends one row per (item, arm) to evaluation/results/agent_comparison.jsonl and
stops cleanly when the quota runs out; run it again the next day to resume.
Writes the paired summary to evaluation/results/agent_comparison.json.

  make compare-agent                          # run what is missing, then summarise
  make compare-agent ARGS="--limit 5"         # at most 5 items this run
  make compare-agent ARGS="--summary-only"    # no LLM calls"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from core.logging import setup_logging  # noqa: E402
from evaluation.agent_eval import load_rows, run_comparison, summarize  # noqa: E402
from evaluation.retrieval_eval import load_gold  # noqa: E402
from generation.llm_client import LLMClient  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="items to run this time")
    ap.add_argument("--delay", type=float, default=6.0, help="seconds between LLM calls (per-minute limit)")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    settings = get_settings()
    items = [i for i in load_gold(settings.resolve(settings.evaluation.gold_path))
             if i.kind == "multi_hop" and i.reviewed_by == "human" and not i.expect_refusal]
    out = settings.resolve(settings.agent.comparison_out)
    status = 0
    if not args.summary_only:
        llm = LLMClient(settings)
        if not llm.available:
            print("GEMINI_API_KEY is not set; nothing run (use --summary-only to summarise).")
            return 1
        from retrieval.pipeline import build_pipeline  # loads the models: only when running

        written, stopped = run_comparison(items, settings, build_pipeline(settings), llm, out,
                                          limit=args.limit, delay_s=args.delay)
        print(f"{written} new rows in {out.name}")
        if stopped:
            print(f"stopped at {stopped}; run again later to resume")
            status = 2
    summary = summarize(load_rows(out), items, settings.evaluation.bootstrap_resamples,
                        settings.evaluation.bootstrap_seed)
    settings.resolve(settings.agent.summary_out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
