"""Shared singletons for the API layer. The retrieval pipeline is cached after
first build; /ingest calls reset_pipeline() so the next request sees fresh
indexes."""

import hmac
import os
from functools import lru_cache

from fastapi import Header, HTTPException

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


def require_admin(authorization: str | None = Header(default=None)) -> None:
    """Gate for /ingest and /evaluate. No ADMIN_TOKEN on the server = the routes do not exist (404),
    so a deployed app never exposes them by accident. Read per request, not cached, so a restart is not needed to change it."""
    token = (os.environ.get("ADMIN_TOKEN") or "").strip()  # blank or whitespace = unset, never a guessable token
    if not token:
        raise HTTPException(status_code=404, detail="Not Found")
    # bytes compare: hmac.compare_digest raises TypeError on non-ASCII str, which would be a 500
    if not hmac.compare_digest((authorization or "").encode(), f"Bearer {token}".encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
