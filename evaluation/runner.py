"""The 4-way benchmark: vector-only / bm25-only / hybrid / hybrid+rerank over
the gold set. Writes benchmark.json for the dashboard and refreshes the README
table between the marker comments."""

import json
import logging
import re
import time
from datetime import datetime, timezone

from core.config import REPO_ROOT, Settings
from evaluation.answer_eval import METHOD_LABEL, evaluate_answer
from evaluation.latency_eval import summarize_latencies
from evaluation.retrieval_eval import count_relevant_chunks, evaluate_ranking, load_gold
from generation.answer_generator import generate_answer
from generation.llm_client import LLMClient
from retrieval.pipeline import MODES, build_pipeline
from schemas.eval import AnswerMetrics, BenchmarkResult, ConfigMetrics

log = logging.getLogger(__name__)

README_START = "<!-- BENCHMARK:START -->"
README_END = "<!-- BENCHMARK:END -->"


def run_benchmark(settings: Settings) -> BenchmarkResult:
    pipeline = build_pipeline(settings)
    gold = load_gold(settings.resolve(settings.evaluation.gold_path))
    corpus = list(pipeline.chunks.values())
    ks = settings.evaluation.k_values
    eval_k = max(ks)

    # items with no relevant docs are refusal probes; retrieval metrics skip them
    gold_retrieval = [g for g in gold if g.relevant_doc_ids]
    total_relevant = {g.qid: count_relevant_chunks(corpus, g) for g in gold_retrieval}

    configs: list[ConfigMetrics] = []
    for mode in MODES:
        per_query, latencies = [], []
        for item in gold_retrieval:
            start = time.perf_counter()
            results = pipeline.search(item.question, mode=mode, top_k=eval_k)
            latencies.append((time.perf_counter() - start) * 1000)
            ranked = [rc.chunk for rc in results]
            per_query.append(evaluate_ranking(ranked, item, ks, total_relevant[item.qid]))

        n = len(per_query)
        lat = summarize_latencies(latencies)
        configs.append(ConfigMetrics(
            name=mode,
            recall={f"@{k}": round(sum(q["recall"][f"@{k}"] for q in per_query) / n, 3) for k in ks},
            mrr=round(sum(q["rr"] for q in per_query) / n, 3),
            ndcg={f"@{k}": round(sum(q["ndcg"][f"@{k}"] for q in per_query) / n, 3) for k in ks},
            latency_p50_ms=lat["p50_ms"],
            latency_p95_ms=lat["p95_ms"],
        ))
        log.info("benchmark mode=%s done (p50=%sms)", mode, lat["p50_ms"])

    answers = _answer_metrics(settings, pipeline, gold)

    result = BenchmarkResult(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        gold_size=len(gold_retrieval),
        chunk_count=len(corpus),
        settings_snapshot={
            "rrf_k": settings.retrieval.rrf_k,
            "rerank_n": settings.retrieval.rerank_n,
            "refusal_threshold": settings.generation.refusal_threshold,
            "embed_model": settings.models.embed_model,
            "rerank_model": settings.models.rerank_model,
        },
        configs=configs,
        answers=answers,
    )
    _write_outputs(settings, result)
    return result


def _answer_metrics(settings, pipeline, gold) -> AnswerMetrics:
    llm = LLMClient(settings)
    stats, refusals = [], 0
    for item in gold:
        retrieved = pipeline.search(item.question, mode="hybrid_rerank")
        draft = generate_answer(item.question, retrieved, settings, llm)
        if draft.refused:
            refusals += 1
            continue
        s = evaluate_answer(draft.text, draft.refused, draft.evidence)
        if s:
            stats.append(s)

    total_claims = sum(s["claims"] for s in stats)
    supported = sum(s["supported"] for s in stats)
    groundedness = supported / total_claims if total_claims else 0.0
    return AnswerMetrics(
        groundedness=round(groundedness, 3),
        unsupported_claim_rate=round(1 - groundedness, 3) if total_claims else 0.0,
        refusal_rate=round(refusals / len(gold), 3) if gold else 0.0,
        method=METHOD_LABEL,
    )


def _write_outputs(settings: Settings, result: BenchmarkResult) -> None:
    out_path = settings.resolve(settings.evaluation.benchmark_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    log.info("wrote %s", out_path)

    readme = REPO_ROOT / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        if README_START in content and README_END in content:
            table = render_markdown_table(result)
            pattern = re.compile(re.escape(README_START) + ".*?" + re.escape(README_END), re.DOTALL)
            content = pattern.sub(f"{README_START}\n{table}\n{README_END}", content)
            readme.write_text(content, encoding="utf-8")
            log.info("refreshed README benchmark table")


def render_markdown_table(result: BenchmarkResult) -> str:
    ks = sorted(result.configs[0].recall.keys(), key=lambda s: int(s[1:])) if result.configs else []
    header = "| config | " + " | ".join(f"Recall{k}" for k in ks) + " | MRR | " + \
             " | ".join(f"nDCG{k}" for k in ks) + " | p50 ms | p95 ms |"
    sep = "|" + "---|" * (2 * len(ks) + 4)
    rows = [header, sep]
    for c in result.configs:
        cells = [c.name]
        cells += [f"{c.recall[k]:.3f}" for k in ks]
        cells.append(f"{c.mrr:.3f}")
        cells += [f"{c.ndcg[k]:.3f}" for k in ks]
        cells += [f"{c.latency_p50_ms:.0f}", f"{c.latency_p95_ms:.0f}"]
        rows.append("| " + " | ".join(cells) + " |")
    footer = (
        f"\n_Gold set: {result.gold_size} questions over {result.chunk_count} chunks. "
        f"Generated {result.generated_at}._"
    )
    if result.answers:
        footer += (
            f"\n\n_Answer quality (hybrid+rerank): groundedness {result.answers.groundedness:.3f}, "
            f"unsupported-claim rate {result.answers.unsupported_claim_rate:.3f}, "
            f"refusal rate {result.answers.refusal_rate:.3f} — {result.answers.method}._"
        )
    return "\n".join(rows) + footer


def to_json(result: BenchmarkResult) -> str:
    return json.dumps(result.model_dump(), indent=2)
