# Engineering decisions

Dated log of the calls I made while building this, and why. Newest last.

## 2026-07-24 — custom modules over LangChain/LlamaIndex

Framework RAG hides exactly the things this project exists to show: where
candidates come from, how they're fused, why a chunk won. Writing the ~6
retrieval modules by hand cost maybe a day and means every score in the trace
is explainable. I'd reconsider for a team that needs 20 loaders, not for this.

## 2026-07-25 — structure-aware chunking, whitespace token proxy

Fixed-size chunking chops code examples in half, and half a code block is
worse than none — it looks authoritative and runs into a syntax error.
So: split on headings, pack to 512–1024 tokens, never break a fenced block,
carry ~12% word-level overlap. I count tokens by whitespace instead of BPE;
it's within ~25% on prose, and the budget doesn't need to be exact — it needs
to be consistent. Not worth a tiktoken dependency.

## 2026-07-26 — RRF over weighted score fusion

Dense cosine lives in [0,1]-ish, BM25 is unbounded and corpus-dependent.
Weighted sums need per-corpus score normalization that quietly rots when the
corpus changes. RRF only consumes ranks, has one parameter (k=60, straight
from the Cormack et al. paper), and is deterministic with a lexical
tie-break. Slightly worse than a perfectly tuned weighted fusion in papers;
massively better than a badly tuned one in practice.

## 2026-07-27 — memory vector store first, Qdrant behind the same interface

Local-first constraint for this phase: no containers. Brute-force cosine over
a NumPy matrix is exact (not ANN-approximate), ~instant at this corpus size,
and persists as one .npz file. The Qdrant implementation sits behind the same
build/load/search interface and is selected by `vector_backend` in
settings.yaml, so the swap is config, not code. The interface is three
methods precisely so both backends stay honest.

## 2026-07-28 — bge-small for embeddings, bge-reranker-base for rerank

bge-small-en-v1.5: 384 dims, ~130MB, strong retrieval scores for its size,
tolerable on CPU. The reranker is the expensive piece (~1.1GB, cross-encodes
query×chunk), so it only sees the top rerank_n=10 fused candidates — that's
the latency budget: rerank cost is capped by a config knob, not by corpus
size. I force a sigmoid on the reranker logits so the refusal threshold in
config compares against a stable 0..1 scale regardless of library defaults.

## 2026-07-29 — refuse on weak evidence, threshold on the rerank score

The refusal gate uses the *reranker's* top score, not cosine similarity —
cosine against an embedded query is always "somewhat high" for in-domain
vocabulary, while a cross-encoder actually reads the pair and scores garbage
near zero. Threshold 0.3 chosen by eyeballing scores for on-corpus questions
(consistently >0.9) vs off-corpus ones (<0.05). It's a config knob because
that gap will narrow on messier corpora.

## 2026-07-30 — doc-level gold labels, not chunk ids

First draft labeled relevant chunk_ids. Then I changed the chunker config and
every label rotted. Relevance is now judged at doc level with optional
section-path substrings to narrow it; labels survive re-chunking, which is
the thing you tune most. The tradeoff: recall against doc-level labels is
easier to saturate on a small corpus — noted in the README limitations.

## 2026-07-31 — extractive fallback instead of a mocked LLM

No API key must still mean a working demo, but faking an LLM response would
poison the groundedness numbers. The fallback selects the most query-relevant
prose sentences from each evidence chunk and cites them — dumb, honest, and
grounded by construction. It shares evidence numbering with the LLM path so
the citation mapper and its tests cover both.

## 2026-08-01 — groundedness by token overlap, clearly labeled

An LLM-judge without a key is a mock, and inventing metrics is worse than
crude ones. The overlap heuristic (≥50% of a claim's content words present in
cited evidence) is labeled "token-overlap heuristic (not an LLM judge)" in
the benchmark JSON, the dashboard, and the README. When a key is available,
an LLM judge can slot into answer_eval.py without touching the harness.
