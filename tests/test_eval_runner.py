import json

from core.config import Settings
from evaluation.runner import aggregate, run_benchmark
from schemas.common import Chunk, RetrievedChunk


def test_group_aggregation_is_query_weighted_and_handles_empty_groups():
    rows = [{"metrics": {"recall": {"@5": r}, "rr": r, "ndcg": {"@5": r}}, "latency_ms": ms}
            for r, ms in [(1, 10), (0, 30), (0.5, 20)]]
    metrics = aggregate("vector", rows, [5])
    assert metrics.query_count == 3
    assert metrics.recall == {"@5": 0.5}
    assert metrics.mrr == 0.5 and metrics.latency_p50_ms == 20
    assert aggregate("vector", [], [5]).recall == {"@5": 0.0}


def test_benchmark_reuses_scores_and_cannot_call_live_llm(tmp_path, monkeypatch):
    from evaluation import runner

    settings = Settings(llm_api_key="must-never-be-used")
    settings.evaluation.gold_path = str(tmp_path / "gold.jsonl")
    settings.evaluation.benchmark_out = str(tmp_path / "benchmark.json")
    settings.evaluation.calibration_out = str(tmp_path / "calibration.json")
    settings.evaluation.audit_path = str(tmp_path / "missing-audit.json")
    settings.evaluation.readme_path = str(tmp_path / "README.md")
    settings.paths.verified_dir = str(tmp_path / "verified")
    chunk = Chunk(chunk_id="c", doc_id="d", source="test", title="T", section_path="Admission",
                  url="https://example.org", text="Applicants need an English certificate and a bachelor degree.", token_count=12)
    calls = []

    class Pipeline:
        chunks = {"c": chunk}

        def search(self, query, mode, top_k=None):
            calls.append((query, mode))
            return [RetrievedChunk(chunk=chunk, rerank_score=0.05 if query == "unanswerable" else 0.9)]

    monkeypatch.setattr(runner, "build_pipeline", lambda _: Pipeline())

    def forbidden(*args, **kwargs):
        raise AssertionError("benchmark called a live LLM")

    monkeypatch.setattr(runner.LLMClient, "complete", forbidden)
    items = [{"qid": "a", "question": "English certificate?", "kind": "requirement", "relevant_doc_ids": ["d"]},
             {"qid": "b", "question": "bachelor degree?", "kind": "country_rules", "relevant_doc_ids": ["d"]},
             {"qid": "r", "question": "unanswerable", "kind": "refusal", "relevant_doc_ids": [], "expect_refusal": True}]
    (tmp_path / "gold.jsonl").write_text("".join(json.dumps(i) + "\n" for i in items))
    result = run_benchmark(settings)
    assert settings.llm_api_key == "must-never-be-used" and settings.generation.refusal_threshold == 0.3
    assert result.gold_size == 2 and result.total_gold_size == 3
    assert len(calls) == 1 + 2 * 4 + 1  # model warmup, one pass per mode, single refusal probe
    assert set(result.retrieval_by_kind) == {"requirement", "country_rules"}
    assert result.answers.generation_mode == "extractive"
    details = json.loads((tmp_path / "calibration.json").read_text())
    assert len(details["per_item"]) == 3 and details["answer_confusion"]["true_refusals"] == 1
    assert "gold" in result.input_hashes
