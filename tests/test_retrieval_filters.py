from pathlib import Path

import pytest
from pydantic import ValidationError

from core.config import Settings
from ingestion.registry import load_registry
from retrieval.filters import PROGRAMMES, UNIVERSITIES, detect_filters
from retrieval.pipeline import RetrievalPipeline
from schemas.common import Chunk
from schemas.search import SearchRequest

ROOT = Path(__file__).resolve().parent.parent


def chunk(cid, university=None, programme=None, stage=None, layer="university"):
    return Chunk(chunk_id=cid, doc_id=cid, source="t", title=cid, section_path="s", url="https://x.org",
                 text=f"text of {cid}", token_count=3, university=university, programme=programme,
                 stage=stage, layer=layer)


CHUNKS = {c.chunk_id: c for c in [
    chunk("r1", "RWTH Aachen", "M.Sc. Computer Science"),
    chunk("t2", "TUM", "M.Sc. Data Engineering and Analytics"),
    chunk("t1", "TUM", "M.Sc. Informatics"),
    chunk("t3", "TUM", stage="before_applying"),
    chunk("c1", layer="rules", stage="visa_funds"),
]}
RANKING = list(CHUNKS)  # r1 ranks first, the country rule last


class Ranked:
    def __init__(self):
        self.asked = []

    def search(self, _query, k):
        self.asked.append(k)
        return [(cid, 1.0 / (i + 1)) for i, cid in enumerate(RANKING)][:k]


class Embedder:
    def encode_query(self, query):
        return query


class Reranker:
    def score(self, _query, texts):
        return [float(len(texts) - i) for i in range(len(texts))]  # keeps the fused order


def pipeline(top_k=2):
    settings = Settings()
    settings.retrieval.dense_top_k = settings.retrieval.bm25_top_k = top_k
    settings.retrieval.final_top_k = top_k
    return RetrievalPipeline(settings, Embedder(), Ranked(), Ranked(), Reranker(), CHUNKS)


def ids(results):
    return [r.chunk.chunk_id for r in results]


def test_no_filter_is_the_unfiltered_search():
    p = pipeline()
    plain = [r.model_dump() for r in p.search("q")]
    assert [r.model_dump() for r in p.search("q", filters=None)] == plain
    assert [r.model_dump() for r in p.search("q", filters={})] == plain
    assert set(p.dense.asked) == {2} and set(p.bm25.asked) == {2}  # usual top-k, no corpus scan


def test_university_filter_keeps_country_rules_and_drops_other_universities():
    assert set(ids(pipeline(5).search("q", filters={"university": ["TUM"]}))) == {"t1", "t2", "t3", "c1"}


def test_programme_filter_drops_the_sibling_programme():
    found = ids(pipeline(5).search("q", filters={"university": ["TUM"], "programme": ["M.Sc. Informatics"]}))
    assert set(found) == {"t1", "t3", "c1"}


def test_filtered_search_reaches_past_the_usual_top_k():
    p = pipeline(2)
    assert ids(p.search("q", filters={"stage": ["visa_funds"]})) == ["c1"]  # ranked 5th of 5
    assert p.dense.asked == [len(CHUNKS)]


def test_stage_and_layer_match_exactly():
    assert set(ids(pipeline(5).search("q", filters={"layer": ["university"]}))) == {"r1", "t1", "t2", "t3"}
    assert ids(pipeline(5).search("q", filters={"stage": ["before_applying"]})) == ["t3"]


@pytest.mark.parametrize("query, expected", [
    ("TUM informatics application deadline?", {"university": ["TUM"], "programme": ["M.Sc. Informatics"]}),
    ("TU Berlin computer science maths credits",
     {"university": ["TU Berlin"], "programme": ["M.Sc. Computer Science"]}),
    ("does Karlsruhe charge tuition?", {"university": ["KIT"]}),
    ("how much goes in a blocked account?", {}),
    ("TUM computer science master: GRE?", {"university": ["TUM"], "programme": ["M.Sc. Informatics"]}),
    ("TUDa AI and machine learning english proof",
     {"university": ["TU Darmstadt"], "programme": ["M.Sc. Artificial Intelligence and Machine Learning"]}),
    # another institution in a covered city: no scope, so the coverage refusal still works
    ("what GPA do I need for the LMU Munich data science master?", {}),
    ("FU Berlin computer science deadline", {}),
    ("Hochschule Darmstadt informatik", {}),
])
def test_detector(query, expected):
    assert detect_filters(query) == expected


def test_detector_keeps_both_sides_of_a_comparison():
    found = detect_filters("GRE for TUM data engineering vs Stuttgart")
    assert found["university"] == ["TUM", "University of Stuttgart"]
    assert found["programme"] == ["M.Sc. Computer Science", "M.Sc. Data Engineering and Analytics"]
    # a university whose programme is not named keeps all of its programmes
    found = detect_filters("TUM informatics or RWTH, which is cheaper?")
    assert set(found["programme"]) == {"M.Sc. Informatics", *PROGRAMMES["RWTH Aachen"]}


def test_alias_table_covers_the_registry():
    sources = load_registry(ROOT / "sources" / "registry.yaml")
    assert {s.university for s in sources if s.university} <= set(UNIVERSITIES)
    for s in sources:
        if s.programme:
            assert s.programme in PROGRAMMES[s.university], s.id


def test_api_rejects_unknown_filter_keys_and_empty_lists():
    assert SearchRequest(query="x", filters={"university": ["TUM"]}).filters == {"university": ["TUM"]}
    for bad in ({"country": ["DE"]}, {"university": []}, {"university": ["tum"]}, {"stage": ["visa"]}):
        with pytest.raises(ValidationError):
            SearchRequest(query="x", filters=bad)
