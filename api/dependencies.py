"""Shared singletons for the API layer. The retrieval pipeline is cached after
first build; /ingest calls reset_pipeline() so the next request sees fresh
indexes."""

from functools import lru_cache

from core.config import get_settings
from generation.llm_client import LLMClient
from retrieval.pipeline import RetrievalPipeline, build_pipeline


@lru_cache
def get_retrieval_pipeline() -> RetrievalPipeline:
    return build_pipeline(get_settings())


@lru_cache
def get_llm_client() -> LLMClient:
    return LLMClient(get_settings())


def reset_pipeline() -> None:
    get_retrieval_pipeline.cache_clear()
