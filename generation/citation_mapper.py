"""Maps inline [n] markers back to their source chunks. A marker that doesn't
point at a real evidence slot is treated as hallucinated: stripped from the
text and excluded from the citation list. This matters most on the LLM path,
where nothing else stops the model inventing [7] out of four sources."""

import re

from schemas.answer import Citation
from schemas.common import Chunk

CITE_RE = re.compile(r"\[(\d+)\]")


def map_citations(text: str, evidence: list[Chunk]) -> tuple[str, list[Citation]]:
    seen: set[int] = set()

    def check(match: re.Match) -> str:
        n = int(match.group(1))
        if 1 <= n <= len(evidence):
            seen.add(n)
            return match.group(0)
        return ""  # hallucinated marker

    cleaned = CITE_RE.sub(check, text)
    cleaned = re.sub(r"[ \t]+([.,;:!?)])", r"\1", cleaned)  # tidy gaps left by stripped markers
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()

    citations = [
        Citation(
            marker=n,
            chunk_id=evidence[n - 1].chunk_id,
            url=evidence[n - 1].url,
            title=evidence[n - 1].title,
            section_path=evidence[n - 1].section_path,
        )
        for n in sorted(seen)
    ]
    return cleaned, citations
