"""Retrieval metrics against the hand-labeled gold set. Relevance is judged at
doc level, optionally narrowed by section-path substrings, so the labels
survive re-chunking — labeling individual chunk_ids would rot every time the
chunker config changes."""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from schemas.common import Chunk


@dataclass
class GoldItem:
    qid: str
    question: str
    relevant_doc_ids: list[str]
    relevant_sections: list[str] = field(default_factory=list)
    answer_hint: str = ""


def load_gold(path: Path) -> list[GoldItem]:
    items = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            raw = json.loads(line)
            items.append(GoldItem(
                qid=raw["qid"],
                question=raw["question"],
                relevant_doc_ids=raw["relevant_doc_ids"],
                relevant_sections=raw.get("relevant_sections", []),
                answer_hint=raw.get("answer_hint", ""),
            ))
    return items


def chunk_is_relevant(chunk: Chunk, gold: GoldItem) -> bool:
    if chunk.doc_id not in gold.relevant_doc_ids:
        return False
    if not gold.relevant_sections:
        return True
    path = chunk.section_path.lower()
    return any(s.lower() in path for s in gold.relevant_sections)


def count_relevant_chunks(corpus: list[Chunk], gold: GoldItem) -> int:
    return sum(1 for c in corpus if chunk_is_relevant(c, gold))


def evaluate_ranking(ranked: list[Chunk], gold: GoldItem, ks: list[int],
                     total_relevant: int) -> dict:
    """Recall@k over relevant *docs* found, MRR and binary nDCG@k over the
    chunk ranking."""
    rels = [chunk_is_relevant(c, gold) for c in ranked]

    out: dict = {"recall": {}, "ndcg": {}}
    for k in ks:
        found_docs = {c.doc_id for c, rel in zip(ranked[:k], rels[:k]) if rel}
        out["recall"][f"@{k}"] = len(found_docs) / len(gold.relevant_doc_ids)

        dcg = sum(1.0 / math.log2(i + 2) for i, rel in enumerate(rels[:k]) if rel)
        ideal_hits = min(total_relevant, k)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
        out["ndcg"][f"@{k}"] = dcg / idcg if idcg > 0 else 0.0

    out["rr"] = 0.0
    for i, rel in enumerate(rels):
        if rel:
            out["rr"] = 1.0 / (i + 1)
            break
    return out
