"""Settings loader. Everything tunable lives in config/settings.yaml; a handful
of env vars (keys, service URLs, model overrides) win over the file so deploys
don't need to touch the yaml."""

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "settings.yaml"

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


class PathsCfg(BaseModel):
    sample_dir: str = "data/samples"
    processed_path: str = "data/processed/chunks.jsonl"
    index_dir: str = "data/index"


class ChunkingCfg(BaseModel):
    target_tokens: int = 512
    max_tokens: int = 1024
    overlap_ratio: float = 0.12
    min_section_tokens: int = 40


class RetrievalCfg(BaseModel):
    vector_backend: str = "memory"
    qdrant_url: str = "http://localhost:6333"
    collection: str = "engineerdoc_chunks"
    dense_top_k: int = 20
    bm25_top_k: int = 20
    rrf_k: int = 60
    rerank_n: int = 10
    final_top_k: int = 5


class ModelsCfg(BaseModel):
    embed_model: str = "BAAI/bge-small-en-v1.5"
    rerank_model: str = "BAAI/bge-reranker-base"
    embed_batch_size: int = 16
    llm_model: str = "gpt-4o-mini"


class GenerationCfg(BaseModel):
    refusal_threshold: float = 0.3
    max_evidence_chunks: int = 4
    max_sentences_per_chunk: int = 3


class EvalCfg(BaseModel):
    gold_path: str = "evaluation/datasets/gold_qa.jsonl"
    k_values: list[int] = [5, 10]
    benchmark_out: str = "frontend/public/benchmark.json"


class Settings(BaseModel):
    paths: PathsCfg = PathsCfg()
    chunking: ChunkingCfg = ChunkingCfg()
    retrieval: RetrievalCfg = RetrievalCfg()
    models: ModelsCfg = ModelsCfg()
    generation: GenerationCfg = GenerationCfg()
    evaluation: EvalCfg = EvalCfg()
    openai_api_key: str | None = None

    def resolve(self, rel: str) -> Path:
        """Turn a repo-relative path from the yaml into an absolute one."""
        return REPO_ROOT / rel


_ENV_OVERRIDES = {
    ("retrieval", "qdrant_url"): "QDRANT_URL",
    ("retrieval", "vector_backend"): "VECTOR_BACKEND",
    ("models", "embed_model"): "EMBED_MODEL",
    ("models", "rerank_model"): "RERANK_MODEL",
    ("models", "llm_model"): "LLM_MODEL",
}


def load_settings(config_path: Path | None = None) -> Settings:
    path = config_path or DEFAULT_CONFIG
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = Settings(**raw)
    for (section, field), env_name in _ENV_OVERRIDES.items():
        value = os.environ.get(env_name)
        if value:
            setattr(getattr(settings, section), field, value)
    settings.openai_api_key = os.environ.get("OPENAI_API_KEY") or None
    return settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()
