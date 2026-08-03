from generation.citation_mapper import map_citations
from schemas.common import Chunk


def make_chunk(i: int) -> Chunk:
    return Chunk(
        chunk_id=f"doc/page::{i:03d}", doc_id="doc/page", source="test",
        title=f"Title {i}", section_path=f"Title {i} > Section",
        url=f"https://example.dev/page{i}/", text=f"text {i}", token_count=2,
    )


EVIDENCE = [make_chunk(1), make_chunk(2), make_chunk(3)]


def test_markers_map_to_correct_chunks():
    text, citations = map_citations("Use defaults [1]. Sessions close automatically [3].", EVIDENCE)
    assert [c.marker for c in citations] == [1, 3]
    assert citations[0].chunk_id == "doc/page::001"
    assert citations[1].chunk_id == "doc/page::003"
    assert citations[0].url == "https://example.dev/page1/"
    assert "[1]" in text and "[3]" in text


def test_repeated_marker_yields_one_citation():
    _, citations = map_citations("First [2]. Again [2]. Once more [2].", EVIDENCE)
    assert len(citations) == 1
    assert citations[0].marker == 2


def test_hallucinated_marker_is_stripped():
    text, citations = map_citations("Real claim [1]. Invented claim [7].", EVIDENCE)
    assert [c.marker for c in citations] == [1]
    assert "[7]" not in text
    assert "Invented claim." in text  # text kept, marker gone, punctuation tidy


def test_marker_zero_is_hallucinated():
    text, citations = map_citations("Zero-indexed nonsense [0].", EVIDENCE)
    assert citations == []
    assert "[0]" not in text


def test_no_markers_no_citations():
    text, citations = map_citations("An answer without any citations.", EVIDENCE)
    assert citations == []
    assert text == "An answer without any citations."


def test_empty_evidence_strips_everything():
    text, citations = map_citations("Claim [1]. Claim [2].", [])
    assert citations == []
    assert "[1]" not in text and "[2]" not in text
