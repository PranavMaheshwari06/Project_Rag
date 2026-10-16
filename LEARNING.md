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

### What was built
- `generation/llm_client.py` on Gemini's OpenAI-compatible endpoint (`models.llm_base_url`), with a fallback list (`models.llm_fallback_models`): a 429 moves to the next model.
- `extraction/schemas.py`: `ProgramRequirements`, 17 `Cited` fields, including entrance tests with applies-to and exempt degree-country lists, foreign grade minimums and APS degree countries. Test-name aliases (GRE / GATE / TOEFL spellings).
- `extraction/extract.py` + `make extract`: one call per programme over its own pages plus its university's general pages; JSON mode, pydantic validation, one repair retry, quote check. Drafts in `data/extracted/`.
- `scripts/dump_pages.py` + second-model cross-check: a model from a different family reads the draft and the exact page text and writes a verdict per field to `data/checked/`.
- `extraction/review.py` + `make review`: field next to quote and page, automatic warnings, cross-check verdicts, a tick per field, Save to `data/verified/`.
- Registry: 53 -> 72 sources. Gap pages for RWTH (deadlines, international application, language rules + PDF) and TUM (language certificates); batch 2 = KIT, TU Darmstadt, Stuttgart. 8 -> 13 programmes.

### Why (defend these)
- **Provider behind one thin client + `base_url`.** Gemini speaks the OpenAI API, so switching provider is a config change, not a code change. The free tier was the budget constraint.
- **Tests blank the API key.** Tests must be offline, deterministic and free; the real endpoint is checked once by hand.
- **`Cited` fields: stated (value + verbatim quote + doc id) or not_published.** The quote lets a human verify in seconds and lets code reject hallucinated values (quote not in source = reject). `not_published` is a real answer the eligibility engine turns into "unknown", never a guess.
- **English scores kept as text** (6.5, 88, C1): different tests use different scales; conversion belongs to the Phase 6 rules engine, not the schema.

- **Conditional entrance tests** (GRE or GATE, only for degrees from named countries). The LLM extracts the condition; the Phase 6 engine applies it to the profile. Hard case of "the LLM never decides".
- **One call per programme over full page text, not retrieved chunks.** Each programme is under ~10k words, so the model sees everything; retrieval could miss the one sentence with the deadline.
- **Quote check on words only** (lowercase, punctuation and markdown dropped), so formatting differences don't reject true quotes, and quotes under 2 words are rejected because they would match anywhere.
- **Failures don't stop the run.** Free-tier 503/429 errors are normal; a failed programme is skipped and re-running fills only the gaps.
- **Second-model cross-check from a different model family.** Two models from the same family tend to make the same mistakes; a different family's errors overlap less. The checker can be wrong too, so its suggestions go through the same schema and quote check, and the human tick stays the final gate.
- **Green / amber fields.** The reviewer's time goes where the risk is: amber fields (checker disagrees or a warning fired) are read in full, green ones get a 10-second quote-vs-value check. Every field is still ticked.
- **Warnings are cheap deterministic checks.** A number in the value that is not in the quote catches invented digits; a "not published" field whose keywords appear on the page catches missed fields.
- **Review screen is a separate app from `api/`.** Nothing admin-only can leak into the public service.
- **Drafts, cross-checks and verified records are all committed.** Together they are the audit trail: what the LLM said, what the checker said, what a human signed off. They are also the inputs for the Phase 4 extraction-accuracy numbers.
- **Batch 2 cut from ~7 to 3 universities.** The goal is to deploy soon; every programme costs ~30 min of human verification and free-tier quota. Adding universities later is data-only work.
- **Phase 6 before Phase 5.** The eligibility engine is the product and needs only the verified records; retrieval upgrades need the Phase 4 baseline to be judged and can wait.
- **Uni-wide pages go to every programme of that university** (fees, language rules). Cheaper than duplicating registry entries; the prompt tells the model to take only what applies to the named programme. A ~100k-character TUM tuition page was left out because it would ride along on every TUM call and hit the per-minute token limit.

### Quiz questions (answer later)
1. Why does every extracted field carry a verbatim quote, and what check does the quote enable?
2. Why is "not published" a separate state rather than an empty value?
3. Why does the LLM extract but never decide eligibility?
4. Why give the extractor whole pages instead of top-k retrieved chunks?
5. A quote check passes. Does that prove the value is right? What else can go wrong?
6. Why use a second model from a different family as a checker, and why does its output still go through the quote check?
7. What does a reviewer do differently on a green field and an amber field, and why is every field still ticked?
8. Why commit drafts, cross-checks and verified records instead of only the verified ones?
9. Why was batch 2 cut to three universities, and what does adding a fourth cost?

### DECISIONS entries to write (maintainer, own words)
- [ ] Gemini free tier via the OpenAI-compatible endpoint; model choice and why 2.5-flash was not usable.
- [ ] The `Cited` field design.
- [ ] Second-model cross-check + human tick as the verification design (and committing `data/checked/` as the audit trail).
- [ ] 2026-10-13: batch 2 = KIT, TU Darmstadt, Stuttgart; Phase 6 before Phase 5; Phase 9 is a functional UI and polish moves to Phase 12 after deploy.

### Open findings
- Free-tier rate limits and model availability change without notice (2.5-flash closed to new keys in Oct 2026).
- Gemini free tier is 20 requests/day per model. Model fallback (3.8 -> 3.6 -> 3.5 flash) and response caching become requirements for the deployed chat (Phase 8).
- A cross-check file has no link to the draft it checked, so it goes stale after `make extract --refresh`; re-run the check after every re-extraction.
- The RWTH per-programme language PDF sits behind an id-based URL that can change when RWTH replaces the file; the crawl will show a 404.
- The first cross-checks (Saarland ×2, TU Berlin, TU Dresden, on the 2026-10-08 drafts) flagged 2 missed fields, 1 wrong field and 10 partial ones. Partials clustered in English scores (dropped TOEFL 2026-format and CEFR minimums), document lists, and GRE/GATE country conditions; the last led to the applies-to / exempt country fields.
- Schema gaps found by the 2026-10-16 cross-checks, for Phase 6 to handle (optional fields added later keep verified records valid):
  - alternative admission routes: KIT CS admits on subject credits **or** a GATE pass **or** a selection interview;
  - exemptions by citizenship or schooling, not degree country: RWTH Data Science waives the GRE for EU/EEA citizens and German school leavers;
  - deadline groups beyond eu / non_eu: RWTH gives non-EU applicants already enrolled at RWTH or holding a German degree 15 July / 15 January;
  - test validity: KIT accepts GRE scores up to 5 years old and GATE up to 3;
  - conditions on a single route: KIT asks for proof of the top 10% only from interview-route applicants.
