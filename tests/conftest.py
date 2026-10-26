"""Shared fixtures. The session-scoped corpus fixture runs the real ingestion
and indexing once, so smoke/e2e tests exercise the same path a user does.
First run downloads the embedding + reranker models."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# tests never call the real LLM: an empty value wins over .env (load_dotenv does not override)
os.environ["GEMINI_API_KEY"] = ""

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def built_corpus(tmp_path_factory):
    from core.config import get_settings
    from ingestion.pipeline import run_ingestion
    from retrieval.pipeline import build_indexes

    settings = get_settings()
    # isolate generated artifacts from the real data/, benchmark.json and README
    tmp = tmp_path_factory.mktemp("rag")
    # offline fixture corpus with known answers, read through the real loader
    settings.paths.registry_path = str(FIXTURES / "registry.yaml")
    settings.paths.manifest_path = str(FIXTURES / "manifest.json")
    settings.paths.raw_dir = str(FIXTURES / "raw")
    settings.evaluation.gold_path = str(FIXTURES / "gold_qa.jsonl")
    settings.paths.processed_path = str(tmp / "chunks.jsonl")
    settings.paths.index_dir = str(tmp / "index")
    settings.evaluation.benchmark_out = str(tmp / "benchmark.json")
    settings.evaluation.readme_path = str(tmp / "README.md")
    stats = run_ingestion(settings)
    build_indexes(settings)
    return stats


@pytest.fixture(scope="session")
def client(built_corpus):
    from fastapi.testclient import TestClient

    from api import dependencies
    from api.main import create_app

    dependencies.get_retrieval_pipeline.cache_clear()
    with TestClient(create_app()) as tc:
        yield tc
