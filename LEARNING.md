# Learning log

One section per phase, appended as each phase is built. Quizzes and `DECISIONS.md` entries are done in one batch after Phase 10 (before Phase 11), so nothing here blocks building. The `DECISIONS.md` entries are written by the maintainer, in their own words.

Per phase: what was built, why (interview answers), quiz questions, the DECISIONS entry owed, open findings.

---

## Phase 2: Sources and ingestion

### What was built
- `sources/registry.yaml`: 53 hand-picked official URLs (country rules, scholarships, 5 pilot universities), validated by `ingestion/registry.py`.
- `ingestion/crawler.py` (`make crawl`): the only network code. Polite (robots.txt, per-host delay, size cap), caches raw files, writes a receipt per page to `sources/manifest.json`.
- Parse (BeautifulSoup / pdfplumber), clean, chunk on headings, provenance copied onto every chunk (`make ingest`), then dense + BM25 indexes (`make index`).
- Result: 53 docs -> 415 chunks (rules 199, scholarship 19, university 197), 0 truncated at the embedder limit.

### Why (defend these)
- **Crawl is separate from ingest.** Downloading is slow, flaky and rude to repeat. Download once; parsing, chunking and indexing are then offline, fast and repeatable.
- **No per-site scrapers.** CSS selectors break when a university redesigns. Saving the page and extracting from plain text survives redesigns.
- **robots.txt fails closed; bot walls are dropped.** If robots.txt can't be read, assume "not allowed" (Deutschlandstipendium was skipped once, fetched fine on retry). "Make it in Germany" showed a bot wall, so it was dropped (BAMF + Service Berlin used instead), not worked around.
- **Provenance on every chunk** (URL, university, programme, stage, layer, crawl date). Without it you can't cite, filter, or tell a user a page is out of date.
- **Registry validated on load.** A typo in a label fails immediately instead of making chunks nobody can filter on.
- **Two indexes.** Embeddings match meaning ("money to prove" ~ "blocked account"); BM25 matches exact words ("APS", "§16b"). Phase 5 combines them.
- **Chunk limit uses the real tokenizer as a second pass.** The whitespace proxy was fine for English prose but German text and tables run up to 2.7 model tokens per word, so 16 of 398 chunks overflowed bge-small's 512 limit and lost their tails. Chunks over `model_token_limit` are now re-split using the embedder's tokenizer.

### Quiz questions (answer later)
1. Why is `crawl` a separate step from `ingest`? What breaks if they are one command?
2. The crawler fails closed when robots.txt is unreachable. What is the cost of that choice and why accept it?
3. Why extract from saved plain text instead of writing a scraper per university site?
4. What does each chunk carry besides its text, and which later phase depends on each field?
5. Why do you need both embeddings and BM25 for this corpus? Give one query where each wins.
6. The word-count proxy for tokens failed on German tables. How was it found, and how was it fixed without dropping the proxy?

### DECISIONS entries to write (maintainer, own words)
- [ ] Phase 2: crawl vs ingest, robots.txt fail-closed, dropping Make it in Germany.
- [ ] 2026-10-06 scope change: Germany only (UK/US dropped), batch 2 at end of Phase 3, agent before deploy, MCP after deploy.
- [ ] Chunk limit: real tokenizer as a second pass (supersedes part of the 2026-07-25 whitespace-proxy entry).

### Open findings
- A forced re-fetch of `de/rules/daad-enrolling` reported `changed=True` for the same URL hours later: pages with dynamic content change their hash without the text changing. The Phase 10 weekly re-crawl uses this hash, so it may be noisy. Fix idea: hash the cleaned text, not the raw bytes.
- The TU Berlin suitability PDF dates from 2020; check currency when extracting in Phase 3.

---

## Phase 3: Extraction + batch 2 (in progress)

### Why (defend these)
- **Provider behind one thin client + `base_url`.** Gemini speaks the OpenAI API, so switching provider is a config change, not a code change. The free tier was the budget constraint.
- **Tests blank the API key.** Tests must be offline, deterministic and free; the real endpoint is checked once by hand.
- **`Cited` fields: stated (value + verbatim quote + doc id) or not_published.** The quote lets a human verify in seconds and lets code reject hallucinated values (quote not in source = reject). `not_published` is a real answer the eligibility engine turns into "unknown", never a guess.
- **English scores kept as text** (6.5, 88, C1): different tests use different scales; conversion belongs to the Phase 6 rules engine, not the schema.

- **Conditional entrance tests** (GRE or GATE, only for degrees from named countries). The LLM extracts the condition; the Phase 6 engine applies it to the profile. Hard case of "the LLM never decides".
- **One call per programme over full page text, not retrieved chunks.** Each programme is under ~10k words, so the model sees everything; retrieval could miss the one sentence with the deadline.
- **Quote check on words only** (lowercase, punctuation and markdown dropped), so formatting differences don't reject true quotes, and quotes under 2 words are rejected because they would match anywhere.
- **Failures don't stop the run.** Free-tier 503/429 errors are normal; a failed programme is skipped and re-running fills only the gaps.

### Quiz questions (answer later)
1. Why does every extracted field carry a verbatim quote, and what check does the quote enable?
2. Why is "not published" a separate state rather than an empty value?
3. Why does the LLM extract but never decide eligibility?
4. Why give the extractor whole pages instead of top-k retrieved chunks?
5. A quote check passes. Does that prove the value is right? What else can go wrong?

### DECISIONS entries to write (maintainer, own words)
- [ ] Gemini free tier via the OpenAI-compatible endpoint; model choice and why 2.5-flash was not usable.
- [ ] The `Cited` field design.

### Open findings
- Free-tier rate limits and model availability change without notice (2.5-flash closed to new keys in Oct 2026).
