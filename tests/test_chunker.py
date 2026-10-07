from core.config import ChunkingCfg
from ingestion.chunker import chunk_document, count_tokens
from ingestion.parser import ParsedDoc


def make_doc(text: str) -> ParsedDoc:
    return ParsedDoc(
        doc_id="test/doc", source="test", url="https://example.dev/doc/",
        title="Test Doc", text=text,
    )


def fence_lines(chunk_text: str) -> int:
    return sum(1 for line in chunk_text.splitlines() if line.strip().startswith("```"))


def test_code_fence_never_split():
    code = "```python\n" + "\n".join(f"x_{i} = {i}" for i in range(60)) + "\n```"
    text = "\n\n".join([
        "# Test Doc",
        " ".join(f"intro{i}" for i in range(50)),
        code,
        " ".join(f"outro{i}" for i in range(50)),
    ])
    cfg = ChunkingCfg(target_tokens=40, max_tokens=50, overlap_ratio=0.1, min_section_tokens=5)
    chunks = chunk_document(make_doc(text), cfg)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert fence_lines(chunk.text) % 2 == 0, "chunk boundary landed inside a code fence"
    # the whole block survived intact in exactly one chunk
    holders = [c for c in chunks if code in c.text]
    assert len(holders) == 1


def test_oversized_code_block_becomes_own_chunk():
    code = "```python\n" + "\n".join(f"line_{i} = {i}" for i in range(200)) + "\n```"
    cfg = ChunkingCfg(target_tokens=50, max_tokens=80, overlap_ratio=0.1, min_section_tokens=5)
    chunks = chunk_document(make_doc(f"# Test Doc\n\nsome intro text here\n\n{code}"), cfg)
    holders = [c for c in chunks if code in c.text]
    assert len(holders) == 1


def test_overlap_carries_tail_of_previous_chunk():
    words = " ".join(f"w{i}" for i in range(300))
    cfg = ChunkingCfg(target_tokens=100, max_tokens=100, overlap_ratio=0.15, min_section_tokens=5)
    chunks = chunk_document(make_doc(f"# Test Doc\n\n{words}"), cfg)

    assert len(chunks) >= 2
    budget = int(cfg.target_tokens * cfg.overlap_ratio)
    for prev, nxt in zip(chunks, chunks[1:]):
        tail = " ".join(prev.text.split()[-budget:])
        assert nxt.text.startswith(tail), "next chunk should start with the previous tail"


def test_split_on_headings_with_section_paths():
    section_a = " ".join(f"alpha{i}" for i in range(80))
    section_b = " ".join(f"beta{i}" for i in range(80))
    text = f"# Test Doc\n\n## First Part\n\n{section_a}\n\n## Second Part\n\n{section_b}"
    cfg = ChunkingCfg(target_tokens=60, max_tokens=200, overlap_ratio=0.1, min_section_tokens=10)
    chunks = chunk_document(make_doc(text), cfg)

    paths = [c.section_path for c in chunks]
    assert any("First Part" in p for p in paths)
    assert any("Second Part" in p for p in paths)
    for chunk in chunks:
        assert chunk.doc_id == "test/doc"
        assert chunk.url == "https://example.dev/doc/"
        assert chunk.chunk_id.startswith("test/doc::")
        assert chunk.token_count == count_tokens(chunk.text)


def test_tiny_sections_merge():
    text = "# Test Doc\n\n## A\n\nshort one.\n\n## B\n\nalso short.\n\n## C\n\nstill short."
    cfg = ChunkingCfg(target_tokens=512, max_tokens=1024, overlap_ratio=0.1, min_section_tokens=40)
    chunks = chunk_document(make_doc(text), cfg)
    assert len(chunks) == 1


def test_chunks_respect_real_model_limit():
    # fake tokenizer: every word costs 3 model tokens, like German text or tables
    tokens_of = lambda text: 3 * len(text.split())  # noqa: E731
    cfg = ChunkingCfg(target_tokens=100, max_tokens=120, overlap_ratio=0.1,
                      min_section_tokens=5, model_token_limit=150)
    doc = make_doc("# Title\n\n" + " ".join(f"w{i}" for i in range(110)))
    chunks = chunk_document(doc, cfg, tokens_of)
    assert len(chunks) > 1
    assert all(tokens_of(c.text) <= cfg.model_token_limit for c in chunks)
