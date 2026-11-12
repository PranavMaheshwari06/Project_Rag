"""Four retrieval modes, extraction audit, and offline refusal calibration."""

import hashlib
import json
import logging
import re
import time
from collections import Counter
from datetime import datetime, timezone

from core.config import Settings
from evaluation.answer_eval import METHOD_LABEL, evaluate_answer
from evaluation.bootstrap import bootstrap_ci
from evaluation.extraction_eval import compare, summarize
from evaluation.latency_eval import summarize_latencies
from evaluation.refusal_eval import calibrate, confusion
from evaluation.retrieval_eval import count_relevant_chunks, evaluate_ranking, load_gold
from generation.answer_generator import generate_answer
from generation.llm_client import LLMClient
from retrieval.pipeline import MODES, build_pipeline
from schemas.eval import AnswerMetrics, BenchmarkResult, ConfigMetrics

log = logging.getLogger(__name__)
README_START = "<!-- BENCHMARK:START -->"
README_END = "<!-- BENCHMARK:END -->"


def aggregate(mode: str, rows: list[dict], ks: list[int], resamples: int = 0, seed: int = 0) -> ConfigMetrics:
    n = len(rows)
    lat = summarize_latencies([r["latency_ms"] for r in rows])
    ci = resamples > 0 and n > 0
    return ConfigMetrics(
        name=mode, query_count=n,
        recall={f"@{k}": round(sum(r["metrics"]["recall"][f"@{k}"] for r in rows) / n, 3)
                if n else 0.0 for k in ks},
        mrr=round(sum(r["metrics"]["rr"] for r in rows) / n, 3) if n else 0.0,
        ndcg={f"@{k}": round(sum(r["metrics"]["ndcg"][f"@{k}"] for r in rows) / n, 3)
              if n else 0.0 for k in ks},
        latency_p50_ms=lat["p50_ms"], latency_p95_ms=lat["p95_ms"],
        recall_ci={f"@{k}": bootstrap_ci([r["metrics"]["recall"][f"@{k}"] for r in rows], resamples, seed)
                   for k in ks} if ci else {},
        mrr_ci=bootstrap_ci([r["metrics"]["rr"] for r in rows], resamples, seed) if ci else None,
    )


def run_benchmark(settings: Settings) -> BenchmarkResult:
    # Never consume live LLM quota, including when .env contains an API key.
    settings = settings.model_copy(deep=True)
    settings.llm_api_key = None
    pipeline = build_pipeline(settings)
    gold = load_gold(settings.resolve(settings.evaluation.gold_path))
    if not gold:
        raise ValueError("the gold set must not be empty")
    corpus = list(pipeline.chunks.values())
    ks = settings.evaluation.k_values
    if not ks or min(ks) < 1:
        raise ValueError("k_values must contain positive integers")
    gold_retrieval = [g for g in gold if g.relevant_doc_ids]
    # Load both models before recording query latency; downloads/loading are
    # startup costs, not steady-state retrieval latency.
    pipeline.search(gold[0].question, mode="hybrid_rerank", top_k=max(ks))
    total_relevant = {g.qid: count_relevant_chunks(corpus, g) for g in gold_retrieval}
    boot = (settings.evaluation.bootstrap_resamples, settings.evaluation.bootstrap_seed)
    cache, retrieval_rows, configs = {}, {}, []
    by_kind = {kind: [] for kind in sorted({g.kind for g in gold_retrieval})}
    for mode in MODES:
        rows = []
        for item in gold_retrieval:
            start = time.perf_counter()
            results = pipeline.search(item.question, mode=mode, top_k=max(ks))
            latency = (time.perf_counter() - start) * 1000
            metrics = evaluate_ranking([r.chunk for r in results], item, ks, total_relevant[item.qid])
            rows.append({"qid": item.qid, "kind": item.kind, "metrics": metrics, "latency_ms": latency})
            if mode == "hybrid_rerank":
                cache[item.qid] = results
                if len(rows) % 10 == 0:
                    log.info("benchmark rerank progress=%d/%d", len(rows), len(gold_retrieval))
        retrieval_rows[mode] = rows
        configs.append(aggregate(mode, rows, ks, *boot))
        for kind in by_kind:
            by_kind[kind].append(aggregate(mode, [r for r in rows if r["kind"] == kind], ks, *boot))
        log.info("benchmark mode=%s done (%d queries)", mode, len(rows))

    for item in gold:
        if item.qid not in cache:
            cache[item.qid] = pipeline.search(item.question, mode="hybrid_rerank")
    scores = []
    for item in gold:
        retrieved = cache[item.qid]
        scores.append({
            "qid": item.qid, "kind": item.kind, "question": item.question,
            "expect_refusal": item.expect_refusal or not bool(item.relevant_doc_ids),
            "has_results": bool(retrieved),
            "top_score": float(retrieved[0].rerank_score or 0.0) if retrieved else 0.0,
            "top_doc_id": retrieved[0].chunk.doc_id if retrieved else None,
        })
    calibration = calibrate(scores, settings.generation.refusal_threshold,
                            settings.evaluation.max_false_refusal_rate)
    settings.generation.refusal_threshold = calibration["selected_threshold"]
    answers, drafts = _answer_metrics(settings, gold, cache, scores)
    for row, draft in zip(calibration["per_item"], drafts):
        row["answer_refused"] = draft.refused
        row["answer_mode"] = draft.mode
    calibration["answer_confusion"] = answers.refusal_confusion
    calibration["retrieval_per_query"] = retrieval_rows
    calibration_path = settings.resolve(settings.evaluation.calibration_out)
    calibration_path.parent.mkdir(parents=True, exist_ok=True)

    audit_path = settings.resolve(settings.evaluation.audit_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    extraction_rows = compare(settings)
    hashes = {}
    for label, path in {"gold": settings.evaluation.gold_path, "chunks": settings.paths.processed_path,
                        "registry": settings.paths.registry_path, "manifest": settings.paths.manifest_path}.items():
        file = settings.resolve(path)
        if file.exists():
            hashes[label] = hashlib.sha256(file.read_bytes()).hexdigest()
    calibration["input_hashes"] = hashes
    calibration_path.write_text(json.dumps(calibration, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result = BenchmarkResult(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        gold_size=len(gold_retrieval), total_gold_size=len(gold), chunk_count=len(corpus),
        gold_counts=dict(Counter(g.kind for g in gold)),
        reviewer_counts=dict(Counter(g.reviewed_by for g in gold)),
        settings_snapshot={
            "rrf_k": settings.retrieval.rrf_k, "rerank_n": settings.retrieval.rerank_n,
            "refusal_threshold": settings.generation.refusal_threshold,
            "embed_model": settings.models.embed_model, "rerank_model": settings.models.rerank_model,
            "generation_mode": "extractive",
            "latency_method": "warm CPU models; actual uncached query timings",
            "bootstrap_resamples": boot[0], "bootstrap_seed": boot[1],
        },
        configs=configs, retrieval_by_kind=by_kind, answers=answers,
        extraction={"human": summarize(extraction_rows), "all": summarize(extraction_rows, None)},
        audit={k: audit[k] for k in ("audited", "of", "seed", "scores", "limitations")} if audit else None,
        refusal_calibration={k: v for k, v in calibration.items()
                             if k not in {"sweep", "per_item", "retrieval_per_query"}}
                            | {"details_path": settings.evaluation.calibration_out},
        input_hashes=hashes,
    )
    _write_outputs(settings, result)
    return result


def _answer_metrics(settings, gold, cache, scores):
    llm = LLMClient(settings)
    stats, drafts = [], []
    for item in gold:
        retrieved = cache[item.qid][:settings.retrieval.final_top_k]
        draft = generate_answer(item.question, retrieved, settings, llm)
        drafts.append(draft)
        if not draft.refused:
            stat = evaluate_answer(draft.text, draft.refused, draft.evidence)
            if stat:
                stats.append(stat)
    total_claims = sum(s["claims"] for s in stats)
    supported = sum(s["supported"] for s in stats)
    groundedness = supported / total_claims if total_claims else 0.0
    return AnswerMetrics(
        groundedness=round(groundedness, 3),
        unsupported_claim_rate=round(1 - groundedness, 3) if total_claims else 0.0,
        refusal_rate=round(sum(d.refused for d in drafts) / len(gold), 3),
        method=METHOD_LABEL, generation_mode="extractive",
        refusal_confusion=confusion(scores, [d.refused for d in drafts]),
    ), drafts


def _write_outputs(settings: Settings, result: BenchmarkResult) -> None:
    out_path = settings.resolve(settings.evaluation.benchmark_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    readme = settings.resolve(settings.evaluation.readme_path)
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        if README_START in content and README_END in content:
            pattern = re.compile(re.escape(README_START) + ".*?" + re.escape(README_END), re.DOTALL)
            content = pattern.sub(lambda _: f"{README_START}\n{render_markdown_table(result)}\n{README_END}", content)
            readme.write_text(content, encoding="utf-8")
    log.info("wrote %s", out_path)


def _with_ci(value: float, ci: tuple[float, float] | None) -> str:
    return f"{value:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]" if ci else f"{value:.3f}"


def _retrieval_table(configs: list[ConfigMetrics]) -> str:
    ks = sorted(configs[0].recall, key=lambda s: int(s[1:])) if configs else []
    rows = ["| config | queries | " + " | ".join(f"Recall{k}" for k in ks) + " | MRR | "
            + " | ".join(f"nDCG{k}" for k in ks) + " | p50 ms | p95 ms |",
            "|" + "---|" * (2 * len(ks) + 5)]
    for c in configs:
        cells = [c.name, str(c.query_count)] + [_with_ci(c.recall[k], c.recall_ci.get(k)) for k in ks]
        cells += [_with_ci(c.mrr, c.mrr_ci)] + [f"{c.ndcg[k]:.3f}" for k in ks]
        cells += [f"{c.latency_p50_ms:.0f}", f"{c.latency_p95_ms:.0f}"]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def render_markdown_table(result: BenchmarkResult) -> str:
    parts = [_retrieval_table(result.configs),
             f"\n_{result.gold_size} answerable questions; {result.total_gold_size} total items; "
             f"{result.chunk_count} chunks. Generated {result.generated_at}._"]
    if any(c.mrr_ci for c in result.configs):
        snap = result.settings_snapshot
        parts.append(f"\n_Brackets: 95% percentile bootstrap interval over queries "
                     f"({snap.get('bootstrap_resamples')} resamples, seed {snap.get('bootstrap_seed')}). "
                     f"Small kinds have wide intervals; read them before comparing configs._")
    for kind, configs in result.retrieval_by_kind.items():
        parts += [f"\n**{kind}**\n", _retrieval_table(configs)]
    if result.extraction:
        parts.append("\n| extraction records | programmes | fields | draft unchanged | checker precision | checker recall |\n"
                     "|---|---|---|---|---|---|")
        for key, label in (("human", "human tier (headline)"), ("all", "all (second_pass not independent)")):
            s = result.extraction[key]
            parts.append(f"| {label} | {s['programmes']} | {s['fields']} | {s['draft_accuracy']} | "
                         f"{s['checker_precision']} | {s['checker_recall']} |")
    if result.audit:
        a = result.audit
        parts.append(f"\n_Historical audit: {a['scores']['strict']['passed']}/{a['audited']} strict passes; "
                     f"{a['scores']['snapshot']['passed']}/{a['audited']} snapshot passes "
                     f"from {a['of']} stated fields (seed {a['seed']}). These are pre-correction results._")
    if result.refusal_calibration:
        c = result.refusal_calibration
        p = c["selected"]
        parts.append(f"\n_Refusal calibration: threshold {c['selected_threshold']:.9g}; "
                     f"{p['true_refusals']}/{p['refusal_count']} probes refused; "
                     f"{p['false_refusals']}/{p['answerable_count']} answerable questions falsely refused. "
                     f"Status: {c['status']}. Calibration-set results, not held-out evaluation._")
        parts.append("\n| probe kind | probes | refused | missed |\n|---|---|---|---|")
        for kind in ("refusal", "coverage"):
            if kind in c["by_kind"]:
                m = c["by_kind"][kind]
                parts.append(f"| {kind} | {m['refusal_count']} | {m['true_refusals']} | {m['missed_refusals']} |")
    if result.answers:
        a = result.answers
        parts.append(f"\n_Answer quality (hybrid+rerank, {a.generation_mode}): groundedness {a.groundedness:.3f}, "
                     f"unsupported-claim rate {a.unsupported_claim_rate:.3f}, refusal rate {a.refusal_rate:.3f} "
                     f"— {a.method}._")
    return "\n".join(parts)


def to_json(result: BenchmarkResult) -> str:
    return result.model_dump_json(indent=2)
