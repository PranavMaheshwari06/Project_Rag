"""Answer quality via a token-overlap heuristic — deliberately simple and
clearly labeled as such everywhere it's reported. A sentence counts as
supported if at least half of its content words appear in the evidence the
answer cites. This is not an LLM judge; it over-credits paraphrase-free
answers (which the extractive mode produces anyway) and under-credits heavy
rewording."""

import re

from generation.answer_generator import SENTENCE_RE, content_words
from schemas.common import Chunk

METHOD_LABEL = "token-overlap heuristic (not an LLM judge)"

SUPPORT_THRESHOLD = 0.5


def _claims(answer_text: str) -> list[str]:
    text = re.sub(r"\[\d+\]", "", answer_text)
    return [s.strip() for s in SENTENCE_RE.split(text) if len(s.strip()) > 10]


def evaluate_answer(answer_text: str, refused: bool, evidence: list[Chunk]) -> dict | None:
    """Returns groundedness stats for one answer, or None for refusals
    (a refusal makes no claims to ground)."""
    if refused:
        return None
    claims = _claims(answer_text)
    if not claims:
        return {"claims": 0, "supported": 0, "groundedness": 0.0}

    evidence_words = content_words(" ".join(c.text for c in evidence))
    supported = 0
    for claim in claims:
        words = content_words(claim)
        if not words:
            supported += 1  # no content words -> nothing to hallucinate
            continue
        if len(words & evidence_words) / len(words) >= SUPPORT_THRESHOLD:
            supported += 1
    return {
        "claims": len(claims),
        "supported": supported,
        "groundedness": supported / len(claims),
    }
