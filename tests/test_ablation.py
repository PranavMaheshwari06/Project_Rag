import json

from core.config import Settings
from evaluation import ablation
from evaluation.retrieval_eval import GoldItem
from schemas.common import Chunk, RetrievedChunk


def chunk(cid, university=None):
    return Chunk(chunk_id=cid, doc_id=cid, source="t", title=cid, section_path="s", url="https://x.org",
                 text=cid, token_count=1, university=university)


TUM, RWTH, RULE = chunk("tum", "TUM"), chunk("rwth", "RWTH Aachen"), chunk("rule")


class Pipeline:
    """Ranks RWTH first; a filter that excludes RWTH lifts the TUM page to rank 1."""
    chunks = {c.chunk_id: c for c in (TUM, RWTH, RULE)}

    def search(self, query, mode, top_k=None, filters=None):
        ranked = [RWTH, TUM, RULE]
        if filters and "university" in filters:
            ranked = [c for c in ranked if c.university in filters["university"] or c.university is None]
        score = 0.05 if query == "unanswerable" else 0.9
        return [RetrievedChunk(chunk=c, rerank_score=score) for c in ranked][:top_k]


def test_arm_filters():
    item = GoldItem(qid="q", question="TUM informatics?", relevant_doc_ids=["tum"], university="TUM")
    assert ablation.arm_filters("baseline", item) is None
    assert ablation.arm_filters("oracle_filter", item) == {"university": ["TUM"]}
    assert ablation.arm_filters("detected_filter", item) == {"university": ["TUM"], "programme": ["M.Sc. Informatics"]}
    assert ablation.arm_filters("oracle_filter", GoldItem(qid="r", question="x", relevant_doc_ids=[])) is None


def test_run_ablation_gains_and_refusals(tmp_path, monkeypatch):
    gold = [{"qid": f"a{i}", "question": "TUM fees?", "relevant_doc_ids": ["tum"], "university": "TUM",
             "reviewed_by": "human" if i else "model"} for i in range(4)]
    gold.append({"qid": "r1", "question": "unanswerable", "relevant_doc_ids": [], "kind": "refusal"})
    path = tmp_path / "gold.jsonl"
    path.write_text("\n".join(json.dumps(g) for g in gold) + "\n")
    settings = Settings()
    settings.evaluation.gold_path = str(path)
    settings.evaluation.k_values = [5]
    settings.evaluation.bootstrap_resamples = 200
    settings.generation.refusal_threshold = 0.1
    monkeypatch.setattr(ablation, "build_pipeline", lambda _: Pipeline())
    result = ablation.run_ablation(settings)
    everyone = result["summary"]["all"]
    assert everyone["baseline"]["mrr"] == 0.5 and everyone["oracle_filter"]["mrr"] == 1.0
    assert everyone["oracle_filter"]["mrr_gain"]["mean"] == 0.5 and everyone["oracle_filter"]["wins"]
    assert "mrr_gain" not in everyone["baseline"]
    assert result["summary"]["human_reviewed"]["baseline"]["query_count"] == 3
    assert result["refusal"]["baseline"] == {"probes": 1, "probes_refused": 1, "answerable": 4, "answerable_refused": 0}
    table = ablation.render_markdown(result)
    assert "**win**" in table and "| baseline | 1/1 | 0/4 |" in table
