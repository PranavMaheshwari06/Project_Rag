"""Latency summaries for the benchmark: p50/p95 plus a rough token count so
cost can be estimated if the LLM path is ever switched on."""

from core.metrics import percentile, rough_token_count


def summarize_latencies(samples_ms: list[float]) -> dict:
    return {
        "p50_ms": round(percentile(samples_ms, 50), 1),
        "p95_ms": round(percentile(samples_ms, 95), 1),
        "mean_ms": round(sum(samples_ms) / len(samples_ms), 1) if samples_ms else 0.0,
        "n": len(samples_ms),
    }


def answer_token_stats(answers: list[str]) -> dict:
    tokens = [rough_token_count(a) for a in answers]
    return {
        "total_answer_tokens_approx": sum(tokens),
        "mean_answer_tokens_approx": round(sum(tokens) / len(tokens), 1) if tokens else 0.0,
    }
