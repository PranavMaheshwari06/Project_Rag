"""End-to-end refusal rate of one-shot RAG with the LLM on, on every gold item except
the multi-hop ones (those are the agent comparison's). Needs GEMINI_API_KEY and the
local indexes. Appends one row per item to evaluation/results/llm_refusal.jsonl and
stops cleanly when the quota runs out; run it again to resume. Writes the summary
to evaluation/results/llm_refusal.json.

  make eval-llm-refusal                        # run what is missing, then summarise
  make eval-llm-refusal ARGS="--limit 10"      # at most 10 items this run
  make eval-llm-refusal ARGS="--summary-only"  # no LLM calls

`--mode auto` measures the escalating mode on top of those one-shot rows: only the items `auto` would escalate
call the agent. Rows go to auto_refusal.jsonl, the summary to auto_refusal.json.

  make eval-llm-refusal ARGS="--mode auto --delay 0 --max-calls 150\""""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from core.logging import setup_logging  # noqa: E402
from evaluation.agent_eval import load_rows  # noqa: E402
from evaluation.llm_refusal_eval import run_auto_item, run_items, summarize, summarize_auto  # noqa: E402
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
    ap.add_argument("--mode", choices=("oneshot", "auto"), default="oneshot")
    ap.add_argument("--max-calls", type=positive, default=None, help="stop before the next item after this many calls")
    args = ap.parse_args(argv)
    setup_logging()
    settings = get_settings()
    items = [i for i in load_gold(settings.resolve(settings.evaluation.gold_path)) if i.kind != "multi_hop"]
    rows_path = settings.resolve(settings.evaluation.llm_refusal_rows_out)
    summary_path = settings.resolve(settings.evaluation.llm_refusal_out)
    run = None
    if args.mode == "auto":
        base_rows = load_rows(rows_path)
        base = {r["qid"]: r for r in base_rows}
        if missing := [i.qid for i in items if i.qid not in base]:
            print(f"{len(missing)} items have no one-shot row yet; run without --mode auto first")
            return 1
        rows_path = settings.resolve(settings.evaluation.auto_refusal_rows_out)
        summary_path = settings.resolve(settings.evaluation.auto_refusal_out)

        def run(item, *rest):
            return run_auto_item(item, base[item.qid], *rest)

    status = 0
    if not args.summary_only:
        llm = LLMClient(settings)
        if not llm.available:
            print("GEMINI_API_KEY is not set; nothing run (use --summary-only to summarise).")
            return 1
        from retrieval.pipeline import build_pipeline  # loads the models: only when running

        pipeline = build_pipeline(settings)
        pipeline.search("warm up", mode="hybrid_rerank", top_k=1)  # model loading is not any item's latency
        written, stopped = run_items(items, settings, pipeline, llm, rows_path,
                                     limit=args.limit, delay_s=args.delay, run=run, max_calls=args.max_calls)
        print(f"{written} new rows in {rows_path.name}")
        if stopped:
            print(f"stopped at {stopped}; run again later to resume")
            status = 2
    resamples, seed = settings.evaluation.bootstrap_resamples, settings.evaluation.bootstrap_seed
    if args.mode == "auto":
        summary = summarize_auto(base_rows, load_rows(rows_path), resamples, seed)
    else:
        summary = summarize(load_rows(rows_path), resamples, seed)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
