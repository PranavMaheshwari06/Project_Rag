# MASTER BUILD PROMPT — EngineerDoc AI

> Paste this into an agentic coding model (Opus in Cursor / Claude Code / Windsurf) with an empty repo open.
> This is a single autonomous build order, NOT a step-by-step tutorial. Build as much as you can in one run.

---

## ROLE

You are a senior AI engineer building a real, deployable Hybrid RAG platform end-to-end in this repository. You write clean, human-looking, modular code. You do NOT use LangChain/LlamaIndex — write custom modules so the architecture is transparent. You do NOT produce toy code, giant files, or AI-flavored over-commenting. Variable names and comments read like a normal engineer wrote them at 11pm.

## PROJECT

Build **PROJECT_RAG**: a production-style hybrid-retrieval RAG service that ingests technical documentation, retrieves with dense + BM25 + Reciprocal Rank Fusion, reranks with a cross-encoder, generates grounded answers with citations, refuses when evidence is weak, exposes everything via FastAPI, and ships a two-tab React frontend (Search + Evaluation Dashboard) plus a reproducible evaluation benchmark. Everything runs from `docker-compose up`.

## NON-NEGOTIABLE PRINCIPLES

1. **Retrieval quality is the product.** The centerpiece deliverable is a 4-way benchmark (vector-only / BM25-only / hybrid / hybrid+rerank) on a small hand-labeled gold set, reporting Recall@k, MRR, nDCG.
2. **Ground or refuse.** Answers use only retrieved evidence, carry inline citations `[1]`, `[2]` mapped to chunk_id + URL, and the system returns an explicit no-answer state when the top rerank score is below a configurable threshold.
3. **Single source of truth for knobs.** All tunable params (top_k, rerank_n, rrf_k=60, refusal_threshold, chunk_size, overlap) live in ONE `config/settings.yaml`, loaded via Pydantic Settings. No magic numbers scattered in code.
4. **Observability by default.** Every request gets a `request_id`; log structured JSON with per-stage latency and a full retrieval trace (dense score, bm25 score, rrf rank, rerank score per chunk).
5. **Honest scale.** v1 is single-node, in-memory BM25, local Qdrant. Do NOT claim or build for 1M PDFs. No OpenSearch, OCR, RBAC, queues, object storage, GraphRAG, or agents.
6. **Modular, small files.** No file over ~250 lines. One responsibility per module.

## TECH STACK

- Backend: FastAPI, Pydantic v2, Uvicorn.
- Vector DB: Qdrant (via docker-compose).
- Dense embeddings: `BAAI/bge-small-en-v1.5` (sentence-transformers).
- Lexical: in-process BM25 (`rank_bm25`).
- Fusion: Reciprocal Rank Fusion, k=60.
- Reranker: cross-encoder `BAAI/bge-reranker-base`.
- LLM: OpenAI via a thin swappable `llm_client` wrapper (read key from env; if no key, fall back to an "extractive" answer mode that stitches top chunks so the app still runs offline).
- Frontend: React + Vite + TypeScript, plain and professional. Recharts for the dashboard charts.
- Packaging: `pyproject.toml`, `Makefile`, Docker + docker-compose.
- Tests: pytest.

## REPO STRUCTURE (create exactly this)

```
engineerdoc-ai/
├── api/
│   ├── main.py
│   ├── dependencies.py
│   ├── routes/            # health.py search.py answer.py ingest.py evaluate.py
│   └── middleware/        # request_id.py logging_mw.py
├── core/
│   ├── config.py          # loads config/settings.yaml via pydantic-settings
│   ├── logging.py         # structured json logging
│   ├── exceptions.py
│   └── metrics.py         # latency timers, token counter
├── schemas/               # search.py answer.py ingest.py eval.py common.py
├── ingestion/
│   ├── sources/           # fastapi_docs.py  extra_source.py
│   ├── crawler.py parser.py cleaner.py chunker.py pipeline.py
├── retrieval/
│   ├── embeddings.py vector_store.py bm25_index.py hybrid.py reranker.py pipeline.py
├── generation/
│   ├── prompt_builder.py llm_client.py answer_generator.py citation_mapper.py
├── evaluation/
│   ├── retrieval_eval.py answer_eval.py latency_eval.py runner.py
│   └── datasets/          # gold_qa.jsonl (seed a few examples + a TODO note)
├── config/
│   └── settings.yaml
├── scripts/               # seed_ingest.py build_indexes.py run_eval.py
├── tests/                 # test_chunker.py test_rrf.py test_citation_mapper.py test_api_smoke.py test_e2e.py
├── data/                  # raw/ processed/ (gitignored except .gitkeep)
├── frontend/              # vite react-ts app, two tabs: Search + Dashboard
├── docker/                # api.Dockerfile frontend.Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
├── Makefile
├── DECISIONS.md           # dated engineering decision log (write real entries as you build)
└── README.md
```

## BUILD ORDER (do all of this in one run; don't stop between)

**A. Scaffold + infra.** Create the tree, `pyproject.toml` with pinned deps, `.env.example` (OPENAI_API_KEY, QDRANT_URL, LLM_MODEL, EMBED_MODEL, RERANK_MODEL), `.gitignore`, `config/settings.yaml`, `core/config.py`, `core/logging.py` (JSON logs with request_id), `core/exceptions.py`, `core/metrics.py`. `Makefile` targets: `install`, `up` (compose), `ingest`, `index`, `eval`, `test`, `run`, `fmt`.

**B. Ingestion.** `crawler.py` loads a bounded set of pages from a local HTML/markdown cache (write `sources/fastapi_docs.py` to fetch or read a small committed sample so the pipeline runs offline). `parser.py` handles HTML + Markdown. `cleaner.py` strips nav/boilerplate, preserves code blocks. `chunker.py` = **structure-aware**: split on headings, target 512–1024 tokens, 10–15% overlap, and never split inside a fenced code block. Each chunk carries metadata: `source, title, section_path, url, doc_id, chunk_id`. `pipeline.py` writes `data/processed/chunks.jsonl`.

**C. Indexing.** `embeddings.py` (batched bge-small). `vector_store.py` (Qdrant create/upsert/search with metadata filters). `bm25_index.py` (rank_bm25 over a code-aware tokenizer; persist to disk). `scripts/build_indexes.py` builds both from chunks.jsonl.

**D. Hybrid retrieval + rerank.** `hybrid.py` runs dense top_k + bm25 top_k, fuses with **RRF (k=60)**. `reranker.py` cross-encodes query×candidate over top rerank_n, returns sorted results with all scores attached. `retrieval/pipeline.py` orchestrates and returns a typed result with the full trace (dense score, bm25 score, rrf rank, rerank score) per chunk.

**E. Grounded generation.** `prompt_builder.py` builds an evidence block with numbered sources. `llm_client.py` = thin wrapper (OpenAI if key present, else extractive fallback). `answer_generator.py` enforces answer-from-evidence-only, emits inline `[n]` citations, and **refuses** ("I don't have enough grounded evidence to answer that.") when top rerank score < refusal_threshold. `citation_mapper.py` maps each `[n]` back to chunk_id + url + title; unit-test this hard.

**F. FastAPI.** Middleware: request_id + structured request/latency logging. Routes: `/health`, `/ingest`, `/search`, `/answer`, `/evaluate`. All request/response bodies are Pydantic schemas. `/answer` returns answer, citations, retrieved chunks with scores, latency breakdown, and a `refused` boolean. `/evaluate` runs the benchmark and returns/writes `benchmark.json`.

**G. Evaluation harness (the spine).** `retrieval_eval.py` computes Recall@k, MRR, nDCG@k against `datasets/gold_qa.jsonl`. `answer_eval.py` computes groundedness + unsupported-claim rate (LLM-judge if key present, else a simple overlap heuristic — clearly labeled). `latency_eval.py` records p50/p95 + token/cost. `runner.py` runs the **4-way benchmark** (vector-only / bm25-only / hybrid / hybrid+rerank) and writes `frontend/public/benchmark.json` + a markdown table into the README (between marker comments). Seed `gold_qa.jsonl` with ~8 real examples and a clear TODO block instructing the human to expand to 30–60 hand-checked pairs.

**H. Frontend (two tabs).**
- **Search tab:** query box → answer with clickable `[n]` citations → retrieved chunks list showing dense/bm25/rerank scores → latency badge → explicit no-answer/refusal state.
- **Evaluation Dashboard tab:** reads `benchmark.json`, renders the 4-way comparison table + Recharts bar charts (Recall@10, MRR, nDCG@10 per config) + latency p50/p95 + unsupported-claim %. This tab must render from the static JSON even with no backend/LLM running.
- Clean, minimal, professional. No auth, no router bloat.

**I. Docker + deploy.** `docker/api.Dockerfile`, `docker/frontend.Dockerfile`, `docker-compose.yml` wiring api + qdrant + frontend with healthchecks. `.env.example` documented. Add a short README section with **Render/Railway** one-service deploy notes (compose-based), so a live URL is achievable.

**J. Tests.** `test_chunker.py` (no code-block splits, overlap correct), `test_rrf.py` (fusion math + tie handling), `test_citation_mapper.py` (n → chunk_id/url correctness, including a hallucinated-citation guard), `test_api_smoke.py` (each endpoint 200s), `test_e2e.py` (ingest tiny sample → index → answer → refuse-on-out-of-corpus). Keep them fast and real.

**K. Docs + human signal.** Write a first-person README: problem framing (naive RAG fails at *retrieval*, not generation), architecture (embed a **Mermaid** query-path diagram), the benchmark table, setup, limitations (single-node, in-memory BM25, clean corpus, small gold set), and a "v2 scale-up: when to add queues/object storage/OpenSearch/OCR/access-control/index-versioning" section. Maintain `DECISIONS.md` with 6–10 dated, opinionated entries reflecting real tradeoffs you made while building (chunking choice, why RRF over weighted fusion, reranker latency budget, embedding model choice). Add 3 resume bullets and a 30-second interview pitch at the bottom of the README.

## GUARDRAILS

- Prefer working code over completeness theater. If a piece needs a secret you don't have, stub it cleanly behind the config/fallback and leave a `# TODO(human):` with exact instructions — never fake it.
- Everything must run offline end-to-end using the committed sample corpus and the extractive fallback (no API key required to demo the pipeline + dashboard).
- Do not invent metrics. Numbers in the README come from actually running `make eval`; before that, use `PENDING` placeholders.
- Commit-sized logical chunks with honest messages as you go (if the agent supports commits).

## STOP CONDITIONS (report, then hand back to me)

Stop and summarize when you reach: (1) expanding the gold eval set beyond the seed (needs my human labeling), (2) real cloud secrets/domain for public deploy, (3) swapping in a paid LLM key. For everything else, keep building until the offline demo works: `make up && make ingest && make index && make eval && make run` produces a live Search + Dashboard.

## FINAL DELIVERABLE OF THIS RUN

A repo where `docker-compose up` (or the Makefile chain) starts Qdrant + API + frontend, the sample corpus ingests and indexes, `/answer` returns a grounded, cited answer AND refuses on an out-of-corpus question, `make eval` regenerates the 4-way benchmark that the Dashboard tab renders, and all tests pass. Then print a short "what's built / what's left for the human" report.
