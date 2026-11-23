"""Turns retrieval output into a grounded answer. Refuses outright when the
top rerank score is under the configured threshold — a weak best hit means the
corpus doesn't cover the question, and stitching something together anyway is
how RAG systems hallucinate.

Answer contract (Phase 8): an LLM answer counts only if at least one [n] marker
points at a real evidence slot. A reply without one gets exactly one repair call;
still uncited, it becomes the refusal. Every refusal says who refused."""

import re
from dataclasses import dataclass, field
from typing import Literal

from core.config import Settings
from generation.llm_client import LLMClient
from generation.citation_mapper import map_citations
from generation.prompt_builder import REFUSAL_TEXT, REPAIR_CITE, build_messages
from schemas.common import Chunk, RetrievedChunk

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
STOPWORDS = frozenset(
    "a an the is are was were be been being do does did to of in on for with and or "
    "not no how what when where which who why can could should would you your it its "
    "this that these those as at by from i my we our".split()
)


# gate: top score under the threshold | model: the LLM gave the refusal text |
# uncited: no valid marker after the one repair | extractive: the no-LLM fallback found no sentence
RefusalReason = Literal["gate", "model", "uncited", "extractive"]


@dataclass
class AnswerDraft:
    text: str
    refused: bool
    mode: str  # "llm" | "extractive" | "refusal"
    evidence: list[Chunk] = field(default_factory=list)
    refusal_reason: RefusalReason | None = None


def _refusal(reason: RefusalReason) -> AnswerDraft:
    return AnswerDraft(text=REFUSAL_TEXT, refused=True, mode="refusal", refusal_reason=reason)


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_]+", text.lower()) if w not in STOPWORDS}


def _prose_sentences(chunk_text: str) -> list[str]:
    """Sentences from the prose parts of a chunk; code fences don't make
    readable answer material."""
    prose_lines = []
    in_fence = False
    for line in chunk_text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and line.strip() and not line.lstrip().startswith("#"):
            prose_lines.append(line.strip())
    sentences = SENTENCE_RE.split(" ".join(prose_lines))
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _extractive_answer(query: str, evidence: list[Chunk], max_sentences: int) -> str:
    """No-LLM mode: pick the query-relevant sentences from each evidence chunk
    and stitch them together with citations."""
    q_words = content_words(query)
    parts = []
    for i, chunk in enumerate(evidence, start=1):
        sentences = _prose_sentences(chunk.text)
        if not sentences:
            continue
        scored = [(len(q_words & content_words(s)), idx, s) for idx, s in enumerate(sentences)]
        picked = sorted(scored, key=lambda t: -t[0])[:max_sentences]
        picked = [p for p in picked if p[0] > 0]
        if not picked and i == 1:
            picked = [scored[0]]  # top-ranked chunk always contributes something
        if not picked:
            continue
        picked.sort(key=lambda t: t[1])  # restore document order
        parts.append(" ".join(s for _, _, s in picked) + f" [{i}]")
    return "\n\n".join(parts) if parts else REFUSAL_TEXT


def generate_answer(query: str, retrieved: list[RetrievedChunk], settings: Settings,
                    llm: LLMClient) -> AnswerDraft:
    threshold = settings.generation.refusal_threshold
    if not retrieved or (retrieved[0].rerank_score or 0.0) < threshold:
        return _refusal("gate")

    evidence = [rc.chunk for rc in retrieved[: settings.generation.max_evidence_chunks]]

    if llm.available:
        messages = build_messages(query, evidence)
        text = llm.complete(messages).strip()
        if text != REFUSAL_TEXT and not map_citations(text, evidence)[1]:  # one repair call, never a loop
            text = llm.complete([*messages, {"role": "assistant", "content": text},
                                 {"role": "user", "content": REPAIR_CITE}]).strip()
        if text == REFUSAL_TEXT:
            return _refusal("model")
        if not map_citations(text, evidence)[1]:
            return _refusal("uncited")
        return AnswerDraft(text=text, refused=False, mode="llm", evidence=evidence)

    text = _extractive_answer(query, evidence, settings.generation.max_sentences_per_chunk)
    if text == REFUSAL_TEXT:
        return _refusal("extractive")
    return AnswerDraft(text=text, refused=False, mode="extractive", evidence=evidence)
