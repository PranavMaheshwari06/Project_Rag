# KICKOFF PROMPT — EngineerDoc AI (local-first, no-Docker phase)

> Paste this whole message into the agent chat. Keep `EngineerDoc_AI_master_build_prompt.md` attached in the same message.

---

Read the attached `EngineerDoc_AI_master_build_prompt.md` in full before writing anything. That file is the authoritative spec — obey its SECRETS POLICY, its "code must not look AI-generated" rules, and its CORRECTNESS BAR literally. This message overrides only the **run/infra mode** for this build session.

## SCOPE OF THIS RUN — local-first, no Docker, no live services

Build and fully verify the project in a local, no-Docker mode. Do NOT require Docker, docker-compose, a running Qdrant container, an API key, or any cloud service to complete the build, tests, or evaluation. Everything must run from a plain Python environment with `uvicorn` and pytest.

Concretely for this run:

- **Repo root is the current folder.** Do NOT create a nested `engineerdoc-ai/` subfolder — scaffold directly here.
- **Vector store:** use Qdrant in embedded/`:memory:` mode via `QdrantClient(":memory:")` (or a local-path client). If that adds friction, implement a small NumPy brute-force cosine vector store behind the SAME interface as the Qdrant one, so I can swap to the real Qdrant container later by changing config only. Put the choice behind `settings.yaml` (`vector_backend: memory|qdrant`).
- **BM25:** in-process (`rank_bm25`), persisted to disk. No server.
- **Embeddings + reranker:** local CPU models (`bge-small-en-v1.5`, `bge-reranker-base`). Download once; keep batches small so CPU is bearable.
- **Answer generation:** use the extractive fallback (no API key). Read the LLM key from env only if present; never generate, invent, or hardcode any key.
- **API:** FastAPI served via `uvicorn` directly (no container).
- **Docker artifacts:** still WRITE `docker/api.Dockerfile`, `docker/frontend.Dockerfile`, and `docker-compose.yml` so they're ready — but they are NOT run or required this session. Mark them clearly as "used in the later containerization phase."

## WHAT TO BUILD THIS RUN (as much as possible, no milestones — one continuous pass)

Build, wire, and verify end to end, in this dependency order, running the relevant tests before moving on and never proceeding on a failing test:

1. Scaffold the full tree from the spec + `pyproject.toml` (pinned deps) + `.gitignore` (exclude `.env`, `data/raw/`, `.venv/`, `node_modules/`, index files) + `config/settings.yaml` + `core/config.py` + `core/logging.py` + `core/exceptions.py` + `core/metrics.py` + a `Makefile` whose targets work WITHOUT Docker (`install`, `ingest`, `index`, `eval`, `test`, `run`).
2. Ingestion: crawler/parser/cleaner/structure-aware chunker/pipeline → `data/processed/chunks.jsonl`, using a small committed HTML/markdown sample so it runs fully offline.
3. Chunker unit tests (no splitting inside code fences, correct overlap) — GREEN before continuing.
4. Indexing: embeddings + the memory/NumPy vector store + BM25, built by `scripts/build_indexes.py`.
5. Hybrid retrieval + RRF (k=60) + cross-encoder reranker + `retrieval/pipeline.py` returning the full per-chunk trace (dense, bm25, rrf rank, rerank score). RRF unit test GREEN.
6. Grounded generation: prompt_builder + llm_client (extractive fallback) + answer_generator (answer-from-evidence-only, inline `[n]` citations, refusal when top rerank score < threshold) + citation_mapper. Citation-mapper unit test (including hallucinated-citation guard) GREEN.
7. FastAPI: request_id + structured logging middleware; routes `/health`, `/ingest`, `/search`, `/answer`, `/evaluate`; Pydantic schemas. API smoke tests GREEN.
8. Evaluation harness: Recall@k/MRR/nDCG + groundedness/unsupported-claim (overlap heuristic, clearly labeled) + latency p50/p95; `runner.py` runs the 4-way benchmark (vector-only/bm25-only/hybrid/hybrid+rerank) and writes `frontend/public/benchmark.json` + a README table between markers. Seed `evaluation/datasets/gold_qa.jsonl` with ~8 real pairs + a `TODO(human)` block to expand to 30–60.
9. Frontend (Vite React-TS): Search tab (query, cited answer, retrieved chunks with dense/bm25/rerank scores, latency badge, refusal state) + Dashboard tab that renders from the static `benchmark.json` (table + Recharts bars + latency + unsupported-claim %). It must render with no backend running.
10. e2e test: ingest tiny sample → index → answer → refuse-on-out-of-corpus. GREEN.
11. README (first-person, Mermaid query-path diagram, benchmark table with `PENDING` until `make eval` is run, honest limitations, v2 scale-up section, 3 resume bullets, 30-sec pitch) + `DECISIONS.md` with 6–10 dated, opinionated, human-voice entries reflecting real tradeoffs you made.

## STOP CONDITIONS (report, then hand back to me)

Stop only when you reach something that genuinely needs me: (1) expanding the gold eval set beyond the seed, (2) flipping from memory vector store to the Docker Qdrant container + running docker-compose, (3) adding a real LLM key, (4) public cloud deploy. For everything else, keep building until this chain works offline: `make install && make ingest && make index && make eval && make run` yields a working API + a Search/Dashboard frontend, and `make test` is fully green.

## BEFORE YOU START

Confirm in ONE line that you've read the spec and understood: no Docker this run, memory/NumPy vector store, extractive fallback, no secrets generated, repo root is the current folder. Then begin with step 1 and keep going without asking further questions you can answer yourself.
