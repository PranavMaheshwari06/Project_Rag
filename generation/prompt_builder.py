"""Builds the grounded prompt for the LLM path. The extractive fallback reuses
the same evidence ordering, so [n] points at the same chunk in both modes."""

from schemas.common import Chunk

REFUSAL_TEXT = "I don't have enough grounded evidence to answer that."

SYSTEM_PROMPT = (
    "You are a technical documentation assistant. Answer the question using ONLY "
    "the numbered evidence passages provided. Every claim must cite its passage "
    "with an inline marker like [1] or [2]. Do not use outside knowledge. If the "
    f'evidence does not answer the question, reply exactly: "{REFUSAL_TEXT}"'
)


def build_evidence_block(evidence: list[Chunk]) -> str:
    parts = []
    for i, chunk in enumerate(evidence, start=1):
        parts.append(f"[{i}] {chunk.title} — {chunk.section_path}\n{chunk.text}")
    return "\n\n".join(parts)


def build_messages(query: str, evidence: list[Chunk]) -> list[dict]:
    user = f"Evidence:\n\n{build_evidence_block(evidence)}\n\nQuestion: {query}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
