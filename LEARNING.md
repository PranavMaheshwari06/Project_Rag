# Learning log

One section per phase, appended as each phase is built. Quizzes are done in one batch after Phase 10 (before Phase 11), so nothing here blocks building.

`DECISIONS.md` entries are drafted from the decisions taken in working sessions (the STATUS log, this file and the plan), dated on the day each was decided, then read and edited by the maintainer into their own words. A ticked box below means the draft is in `DECISIONS.md`.

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
- [x] Phase 2: crawl vs ingest, robots.txt fail-closed, dropping Make it in Germany.
- [x] 2026-10-06 scope change: Germany only (UK/US dropped), batch 2 at end of Phase 3, agent before deploy, MCP after deploy.
- [x] Chunk limit: real tokenizer as a second pass (supersedes part of the 2026-07-25 whitespace-proxy entry).

### Open findings
- A forced re-fetch of `de/rules/daad-enrolling` reported `changed=True` for the same URL hours later: pages with dynamic content change their hash without the text changing. The Phase 10 weekly re-crawl uses this hash, so it may be noisy. Fix idea: hash the cleaned text, not the raw bytes.
- The TU Berlin suitability PDF dates from 2020; check currency when extracting in Phase 3.

---

## Phase 3: Extraction + batch 2

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
- **Second-model cross-check from a different model family.** Two models from the same family tend to make the same mistakes; a different family's errors overlap less. The checker can be wrong too, so its suggestions go through the same schema and quote check, For the first six programmes a human tick was the final gate; batch 2 differs, see the note on how it was verified below.
- **Green / amber fields.** The reviewer's time goes where the risk is: amber fields (checker disagrees or a warning fired) are read in full, green ones get a 10-second quote-vs-value check. Every field is still ticked.
- **Warnings are cheap deterministic checks.** A number in the value that is not in the quote catches invented digits; a "not published" field whose keywords appear on the page catches missed fields.
- **Review screen is a separate app from `api/`.** Nothing admin-only can leak into the public service.
- **Drafts, cross-checks and verified records are all committed.** Together they are the audit trail: what the LLM said, what the checker said, what a human signed off. They are also the inputs for the Phase 4 extraction-accuracy numbers.
- **Batch 2 cut from ~7 to 3 universities.** The goal is to deploy soon; every programme costs ~30 min of human verification and free-tier quota. Adding universities later is data-only work.
- **Batch 2 verified by a second pass over the sources, not by hand.** The first six programmes were ticked field by field in the review screen. For the other seven, to ship sooner, each record was re-read field by field against its cited pages (no outside knowledge) and the corrected records were saved through the same Save path as the screen, so the schema and quote-in-page checks still applied. The first record was checked by hand against the pages before the rest ran, and four calls from the pass were reverted after reading the pages. Rules that came out of it: an example ("e.g. TOEFL 95") is not a minimum; a list is stated only if the page gives the list, so one incidental item stays not_published instead of showing a partial list; an inference (work experience "counts in selection") is not stated unless the page says it; a date is not tagged with an applicant group the page did not name. The cost: for these seven, verified and the cross-check are not independent, so the Phase 4 draft-vs-verified and checker-precision numbers are computed on the six hand-verified programmes and say so.
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
10. Batch 2 was verified by a second source pass instead of a hand tick. What does that change about what "verified" means, and which Phase 4 numbers stay trustworthy?

### DECISIONS entries to write (maintainer, own words)
- [x] Gemini free tier via the OpenAI-compatible endpoint; model choice and why 2.5-flash was not usable.
- [x] The `Cited` field design.
- [x] Second-model cross-check + human tick as the verification design (and committing `data/checked/` as the audit trail).
- [x] 2026-10-13: batch 2 = KIT, TU Darmstadt, Stuttgart; Phase 6 before Phase 5; Phase 9 is a functional UI and polish moves to Phase 12 after deploy.
- [x] 2026-10-23: the seven batch-2 programmes were verified by a second pass over their cited pages instead of a hand tick, to ship sooner; the first six were hand-verified. Phase 4 accuracy numbers use the six.

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
- Batch 2 verification (2026-10-23, 13/13 verified). Changes against the drafts: English tests the page gives only as examples became the stated level (Stuttgart C1); Cambridge "pass" dropped where the page names no score (KIT); work experience set to not_published where it was inferred (TUM x2, Saarland); fuller lists where the page gives one (KIT subject credits, TUM DEA documents); TUM DEA and TU Darmstadt entrance tests now carry their conditions.
- More schema gaps for Phase 6: deadlines have no route (uni-assist vs the direct portal at TU Dresden) and no "recommended, visa applicants only" kind (TUM); aptitude-assessment registration windows (TU Dresden, TUM second stage) have no field; English proof cannot say any-of vs all-of, or hold an English-taught-degree route (Darmstadt) or native-speaker exemptions (Saarland); subject credits cannot say "40 in one area, 12 in each other" (KIT); admission with conditions for up to 12 missing credits (KIT); document lists vary by applicant country (TUM); Darmstadt's semester fee on the page is labelled summer 2025.

---

## Phase 4: Eval baseline (complete locally, 2026-10-27)

All Phase 4 steps are complete locally. The audit and gold acceptance are recorded; `make eval` reports the four modes overall and by kind, extraction accuracy, historical audit results and refusal calibration. PR #4 remains unmerged; Phase 6 follows the closure commit.

### What was built
- **Verification tiers.** Every `data/verified/<slug>.json` has a `tier`: `human` (6 programmes, every field ticked in `make review`) or `second_pass` (7: KIT CDS, Saarland CS, TU Darmstadt AIML, TU Dresden CS, TUM DEA, TUM Informatics, Stuttgart CS). A re-save in `extraction/review.py` keeps the existing tier; promoting `second_pass` to `human` is a deliberate hand edit.
- **Extraction accuracy** (`evaluation/extraction_eval.py`): compares each LLM draft (`data/extracted/`) with its verified record (`data/verified/`) field by field, next to the cross-check verdict (`data/checked/`). `render()` prints the table below.
- **Sampled audit of the second-pass records** (`scripts/audit_sample.py [n] [seed] [--sheet]`): a seeded random sample of `stated` fields from `second_pass` records. `--sheet` writes `data/audit/audit_sheet.md`: for each field the value, quote, doc id, a page excerpt of ±300 characters around the quote, a model pre-check line and an agree/disagree box for the auditor. Run as `scripts/audit_sample.py 35 4 --sheet`: 35 of 69 stated fields, seed 4.
- **Gold set** (`evaluation/datasets/gold_qa.jsonl`, 104 items): requirement 45, country_rules 24, confusable 11, multi_hop 10, refusal 9, coverage 5. Drafted as student-voice questions from the verified pages, then checked by a separate model review pass; the per-item record is `evaluation/datasets/gold_review.md`.
- **Gold fields and validator.** `GoldItem` in `evaluation/retrieval_eval.py` gained optional `kind`, `university`, `programme`, `author`, `reviewed_by` and `expect_refusal`, all defaulted so the old test fixture still loads. `scripts/validate_gold.py` checks every label; `make eval` runs it first.
- 68 tests pass, including review/API/model-backed tests; lint and the frontend production build pass.

### Why (defend these)
- **Tiers instead of hand-ticking all 13.** The seven second-pass records would cost about 30 minutes each to tick by hand. Labelling each record with how it was verified keeps every claim true without blocking the build. The README and every metric say which tier they use.
- **A re-save keeps the tier.** Otherwise opening a second-pass record in the review screen and pressing Save would silently relabel it as human-verified. Promotion is a hand edit so it is always a decision.
- **A sample, not a census.** A random sample of 35 of the 69 stated second-pass fields gives an error-rate estimate with a confidence interval for about half the effort of checking all 69.
- **Seeded.** The same command (`35 4`) always draws the same 35 fields, so anyone can reproduce the sample. The seed is recorded in the sheet and in the audit file, so the sample cannot be quietly redrawn until it looks good.
- **Only `stated` fields are sampled.** The audit measures the precision of stated claims ("when the record says X, is X on the page?"). It does not estimate missed fields; those are what the cross-check's `missed` verdict and the review warnings target.
- **The model pre-check is a second opinion, not the audit.** It points the auditor at likely problems. The auditor can see it, so it is not independent of the human verdict; the audit file records `prechecked_by: model` and `auditor: human` for that reason.
- **Strict accuracy definition.** A field is "unchanged" only if status, value, quote and doc_id are all identical between draft and verified record. The product promises a citation, so a right value with a wrong quote or page is still a correction. The number is conservative: a cosmetic quote trim counts as an edit.
- **Headline on the human tier only.** Second-pass records were verified with the cross-check's help, so they say nothing independent about the draft or the checker.
- **Six kinds of gold item, each testing one thing.** `requirement`: a programme fact from one page. `country_rules`: national rules (visa, APS, blocked account). `confusable`: two sibling programmes whose pages read alike; tests that retrieval finds the right programme, which is where metadata filters (Phase 5) must earn their place. `multi_hop`: needs two docs. `refusal`: the corpus does not answer it. `coverage`: an uncovered university or another country. Splitting metrics by kind shows where a retrieval mode wins or loses instead of one blended average.
- **Refusal and coverage items have no doc ids** (`relevant_doc_ids: []`, `expect_refusal: true`). Retrieval metrics skip them because there is nothing to recall; they feed refusal calibration in step 4.
- **A validator before any number.** A broken label gives a confident wrong metric. The validator catches mechanical errors (unknown doc, a section filter that matches nothing, a number in the hint that is not on the page) before `make eval` runs.
- **Synthetic profiles moved to Phase 6.** They test the eligibility engine, which does not exist yet.

### The numbers

Extraction accuracy (`render()` output):

| records | programmes | fields | draft unchanged | edited | dropped | added | checker precision | checker recall |
|---|---|---|---|---|---|---|---|---|
| human tier (headline) | 6 | 102 | 0.794 | 18 | 0 | 3 | 0.947 | 0.857 |
| all (second_pass not independent) | 13 | 221 | 0.814 | 35 | 3 | 3 | 0.867 | 0.634 |

How to read it:
- **Draft unchanged**: share of fields where the LLM draft survived verification exactly (status, value, quote and doc_id identical). On the human tier, 0.794 of 102 fields; the 0.794 is unchanged from before the tier split.
- **Edited / dropped / added**: stated in both but changed; stated in the draft but `not_published` after verification; `not_published` in the draft but stated after verification.
- **Checker precision**: of the fields the cross-check flagged (wrong, partial or missed), the share that really changed. **Checker recall**: of the fields that changed, the share it flagged.
- **Caveat**: the review screen shows the cross-check verdict next to each field, so the checker numbers mean "predicts what a person who could see its verdict changed". The "all" row includes second-pass records, which were verified with the cross-check's help, so it is not independent; it is shown for completeness, not as the headline.

Audit pre-check on the 35 sampled fields: 33 agree, 2 disagree, 0 unsure. The two disagreements are row 12 (Saarland CS `required_documents` omits the GRE/GATE result and the English certificate that the same section requires) and row 16 (TU Darmstadt AIML `entrance_tests` is recorded as `one_of`, i.e. mandatory, but the page makes the entrance exam conditional, "Only when required entrance competencies cannot be confirmed from the submitted documents", and GRE/GATE an exemption from it; the schema has no "conditional" value). The completed audit covers 35 of the original 69 stated fields (seed 4). Strict passes: 29/35 (82.86%; Wilson 95% interval 0.673–0.919); snapshot passes: 32/35 (91.43%; interval 0.776–0.970). Six confirmed findings (rows 12, 16, 20, 22, 28, 32) were corrected through the review Save path; tiers remain unchanged. These are historical pre-correction scores, not a new accuracy estimate. The original values, completed report, provenance and correction evidence are recorded in `data/audit/second_pass_audit.json`. The remaining 34 stated fields and missed fields are unscored.

Gold set review pass: 107 drafted, 81 unchanged, 23 fixed, 3 dropped, 104 kept. Every retained item is `author: model`, `reviewed_by: human` after maintainer acceptance on 2026-10-27. The maintainer also approved b09/c19 foreign-degree scope, b10 current-semester fee and c05 alternative-source updates. This is assisted review acceptance, not an independent audit of every item.

### How the human steps are done

**(a) Auditing a field (audit sheet row).**
1. Open `data/audit/audit_sheet.md` and, for anything the excerpt does not settle, `make review` on that programme to see the full page.
2. Find the quote on the page. If it is not there word for word (allowing punctuation), stop: that is a disagreement.
3. Check the value against the quote digit by digit: scores, credits, dates, fees. Check country lists name by name (a missing or extra country changes who must take a test).
4. Check scope: does the sentence apply to this programme, this applicant group (EU vs non-EU, degree country) and this intake?
5. Check hard vs recommended: "must", "required" vs "recommended", "should", "e.g.". An example is not a minimum.
6. Read the sentences around the quote for qualifications that change the meaning: "only if", "alternatively", "exempt", "unless". Row 16 is this case.
7. Read the pre-check line last, so it does not anchor you.
8. Tick agree, or tick disagree and write one line saying what the page says instead. Record the totals in `data/audit/second_pass_audit.json` as `{audited, of, seed, auditor: human, prechecked_by: model, disagreements}`. Fix confirmed disagreements in the verified record through the review Save path (which re-runs the schema and quote check); the tier stays `second_pass`.

**(b) Judging a gold item** (skim `evaluation/datasets/gold_review.md`, then the item):
- Do the labelled docs support the answer? Include alternative supporting sources where the question genuinely has multiple valid sources (c05), or reword/drop an ambiguous item. Doc recall then measures source coverage, not whether any single page is sufficient.
- Is the `answer_hint` supported by that doc, numbers included?
- Does the question copy the page's wording? A real student does not write "Zugangsvoraussetzungen"; copied phrases make BM25 look better than it is.
- Is the `kind` right (one doc vs two for `multi_hop`; a real sibling programme for `confusable`)?
- Accept, edit or drop. Set `reviewed_by: human` on accepted or edited items. Optionally write a few items yourself with `author: human`. Run `.venv/bin/python scripts/validate_gold.py` after editing.

**(c) Why 35 of 69 is an estimate, and what k errors means.** Auditing 35 of 69 fields measures the error rate on a sample, so the result is an estimate with uncertainty, not a count. With k errors in n = 35, the observed rate is p = k/n, and the Wilson 95% interval (z = 1.96) gives the range of true error rates consistent with that sample:

- centre = (p + z²/2n) / (1 + z²/n)
- half-width = z · sqrt(p(1−p)/n + z²/4n²) / (1 + z²/n)

| errors k in 35 | Wilson 95% interval for the error rate |
|---|---|
| 0 | [0.000, 0.099] |
| 1 | [0.005, 0.145] |
| 2 | [0.016, 0.186] |
| 3 | [0.030, 0.224] |

Worked example for k = 0: p = 0, z²/n = 3.8416/35 = 0.1098, centre = (0 + 0.0549)/1.1098 = 0.0495, half-width = 1.96 · sqrt(3.8416/4900)/1.1098 = 0.0495, so [0, 0.099]. Zero errors in 35 still allows up to about a 10% error rate. Wilson is used instead of the textbook p ± z·sqrt(p(1−p)/n) because that formula gives a zero-width interval when k = 0, which would claim certainty from a small sample.

**(d) Why model drafting plus human review is defensible.** "Model-assisted, human-reviewed" is a normal way to build an eval set: writing 100 varied questions by hand is slow, while judging whether a drafted question and its label are right is fast and is where a person adds the most. The risks are known and handled: drafted questions can echo page wording (checked in step b), and a model reviewing a model's items shares its blind spots (which is why the human pass exists). `author` and `reviewed_by` are recorded per item so the split is visible to any reader, and metrics can be reported on the human-reviewed subset alone.

### Quiz questions (answer later)
1. A field's value is correct but its quote comes from the wrong page. Does it count as "draft unchanged"? Why is that the right call for this product?
2. Why is the extraction-accuracy headline computed on 6 programmes and not 13?
3. The cross-check has precision 0.947 and recall 0.857 on the human tier. What does each mean, and why are they not independent measurements?
4. The audit finds zero errors in 35 sampled fields. What can you claim about the error rate, and why not "0%"?
5. Why is the audit sample seeded, and why are only `stated` fields sampled? What does that leave unmeasured?
6. Why do refusal and coverage items carry no doc ids, and what are they used for instead?
7. What makes a `confusable` item hard on this corpus, and which later phase is meant to fix it?
8. The gold set is model-drafted. How do you defend it to a reviewer who says "the model graded its own homework"?

### DECISIONS entries to write (maintainer, own words)
- [x] 2026-10-26: verification tiers (`human` / `second_pass`) and a seeded sampled audit instead of hand-ticking all 13.
- [x] 2026-10-26: synthetic profiles moved from Phase 4 to Phase 6.
- [x] 2026-10-26: gold set model-assisted and human-reviewed, with `author` / `reviewed_by` per item.
- [x] 2026-10-26: extraction accuracy defined on value + quote + doc_id.

### Open findings
- Doc-level labels undercount recall when the same fact is stated on two pages (for example RWTH non-EU deadlines on both `de/rwth/application-deadlines` and `de/rwth/master-application-international`). The drafters and the review pass avoided or reworded such items; 3 were dropped. A known limit of doc-level labels.
- Near-identical sibling pages (TUM Informatics vs DEA department pages; TU Darmstadt CS vs AIML programme pages) make confusable items hard to write with a single right answer; only 11 confusables survived.
- Official sources conflict:
  - English level for the visa: India embassy page C1, APS leaflet B2;
  - job-search permit for graduates abroad: BAMF six months, BAMF graduates page up to one year;
  - student residence permit length: BAMF and Aachen one to two years, Munich three years;
  - dMAT timing: APS India home page vs the APS leaflet;
  - student work-day limit: TU Darmstadt guide 140 full / 280 half days, Foreign Office FAQ 120 / 240.
  The answer layer (Phase 8) must surface a conflict with both citations instead of picking one.
- The RWTH language-requirements PDF lost its headings in parsing (all 29 chunks share one `section_path`) and lists two score levels whose scope is unclear.
- Conditional exams now carry an optional `condition`; deadline entries have optional `degree_origin`. Phase 6 must interpret those conditions explicitly and handle the other recorded schema gaps.

### Phase 4 closure measurements

The selected score threshold is `0.13340958034137707`. It refuses 4/14 refusal/coverage probes while falsely refusing 3/90 answerable questions. The constraint is at most 5% false refusals; ties prefer fewer false refusals, then a lower threshold. These are calibration-set results, not held-out estimates. Actual answer refusals are reported separately in the calibration artifact.

The corpus has 74 sources and 600 chunks, with zero embedding truncations. The full four-mode tables and per-kind counts are in the README and benchmark artifact; the score sweep, every qid, actual answer refusals and input hashes are in `evaluation/results/refusal_calibration.json`. The baseline always disables the LLM key; its groundedness is the labelled token-overlap heuristic. Models are warmed before latency measurement.

Optional schema defaults are normalized when comparing extraction records; a changed supporting citation still counts as a correction. All 13 records and their supplemental citations pass validation. The six human-tier programmes remain at 79.4% unchanged over 102 fields, precision 0.947 and recall 0.857.

The review-screen tests stalled in the restricted sandbox and passed outside it. Full test artifacts, including evaluation output, are isolated from real corpus files. CI now covers the new pure-logic and review tests; model-backed API tests remain part of the local full suite.

Additional quiz questions: Why must a threshold sweep reuse scores but latency measurements use real searches? Why does tuning on these probes not establish held-out refusal performance? What does a second valid source change about doc-level Recall@k?

## Phase 6: cited eligibility reports (Step 0 draft, 2026-10-27)

### What is runnable

- `phase-6-eligibility-engine` branches from the completed Phase 4 commit `b85ae75`. PR #4 remains a separate, unmerged prerequisite; nothing was merged during kickoff.
- [The coverage matrix](docs/PHASE_6_RULE_COVERAGE.md) accounts for all 13 programmes and 221 original fields: 24 proposed automatic comparisons, 78 information/readiness fields, 29 manual-review fields and 90 `not_published` fields. These classify possible implementation, not measured engine coverage or eligibility accuracy. No eligibility engine exists yet.
- `data/eligibility/coverage_inventory.json` preserves raw-byte hashes for 51 Phase 4 inputs, canonical hashes of all 13 original records and raw/cleaned hashes for 42 official cached sources. Existing verified records, tiers, audit scores, gold labels and benchmark artifacts remain unchanged.
- [The rule-review packet](docs/PHASE_6_RULE_REVIEW.md) contains 17 pending interpretations and 44 supplemental cached-source excerpts. It exposes the missing KIT CDS thesis prerequisite, conditional Darmstadt exams, RWTH country-basis differences and unresolved language/overlap evidence. It does not claim maintainer acceptance or current live-page verification.
- [The five-profile worksheet](docs/PHASE_6_FIVE_PROFILE_WORKSHEET.md) is deliberately blank. The maintainer writes the facts and expected labels independently before engine comparisons. Filling a form with model labels would not establish independent evaluation.

Run `make validate-phase6-inventory`; locally, add `ARGS="--check-cache"` to parse the official cache and validate original/supplemental quotes and snapshot hashes. The default CI check validates identities, record/baseline bindings and generated-document consistency without pretending raw pages are present. Seven focused tests cover missing inventory fields, stale bindings, changed tiers, source/quote drift, review provenance and baseline preservation. No provider, model download or eligibility verdict is involved.

The extended offline CI selection passes all 55 tests; repository lint and diff whitespace checks pass. As in Phase 4, the review-screen tests stalled in the restricted sandbox and passed outside it. The full model-backed suite and frontend build were not rerun for this inventory-only increment.

### Why these boundaries matter

A quote match checks that words occur in a source, not that a rule interpretation is correct. The derived rule catalogue therefore needs its own semantic review, separate from extraction verification. KIT CS's selection alternatives and its GRE/GATE condition must become separate logical groups. RWTH CS uses degree origin for GRE while DS uses citizenship or German schooling. Treating either distinction as a flat list could reject a qualifying student or exempt one without evidence.

The original `not_published` value also cannot establish that no prerequisite exists. TUM's English fields are empty even though the cached programme pages require language proof; Dresden's required aptitude assessment is under selection rather than entrance tests. Step 0 preserves the historical values and adds a visible gap instead of silently changing the Phase 4 evaluation inputs. Genuine extraction corrections will use the reviewed Save path.

The next steps add typed profiles/rules and deterministic primitives. Consequential semantics remain pending the maintainer's review; unresolved source gaps remain unknown even after accepting that conservative treatment. Academic admission, application readiness and financial checks will have separate summaries. The LLM extracts information; deterministic code compares it.

### Quiz questions (deferred batch)

1. Why can a verified extraction record still be unsafe to use as an executable rule?
2. What false verdict can result from merging KIT's selection routes with GRE/GATE alternatives?
3. How does missing source publication differ from missing student evidence or unresolved university equivalence?
4. What do file, canonical-record and cleaned-source hashes each detect, and what can none of them prove?
5. Why must five maintainer-authored expected labels be frozen before comparing with engine output?

### Pending maintainer work

- Decide R01–R17 (accept, correct or defer) programme by programme as each catalogue is built in Step 3; Steps 1–2 do not wait for them. Source gaps are not resolved by acceptance alone.
- Author five synthetic/anonymised profiles and independent labels using H01–H05 before Step 5 engine comparisons.
- Rewrite the dated Step 0 decision draft in personal words when convenient; quizzes and rewrites retain the deferred schedule.

### Phase 6 Steps 1-3 (2026-10-29): engine primitives and the first rule file

**Maintainer-checked engine behaviour (C1-C10, accepted 2026-10-29).** Hand-checked against `tests/test_eligibility_engine.py`:
- C1-C3: the Bavarian formula, `1 + 3*(best - obtained)/(best - passing)`, gives 2.5 for 3.0 on 4.0/2.0 and for 75 on 100/50, 2.2 for 8 on 10/5, and leaves a German-scale 2.0 at 2.0. The result is an estimate, never an official equivalence.
- C4: a grade outside the scale's passing range is rejected, not converted.
- C5-C7: a minimum of 120 is met at 120 with margin 0 and failed at 119.5 with margin -0.5; a strict bound fails at zero margin; for an upper limit the margin is positive when under it, so positive always means favourable.
- C8: a fact not supplied is `unknown`; a fact entered as 0 is a real failure.
- C9: `any_of` with one fail and one unknown stays unknown; `all_of` with one fail and one unknown fails.
- C10: soft rules and finance/readiness rules never move the academic headline, and an unreviewed rule can never produce a positive headline.

**TUM Informatics decisions.** T1 (R01): degree equivalence is TUM's call, `unknown`, no matching on degree title. T3 (R14): GRE needs QR >= 164 and AW >= 4.0, or a qualifying GATE CS scorecard, only for degrees from Bangladesh, China, India, Iran or Pakistan; the Mechanical Engineering GATE paper is for M.Sc. CSE only. T4 (R14): the aptitude assessment is a university decision, so TUM never shows a positive headline. Those three rules are `reviewed_by: human`. T2 (English) was not accepted blind: see below.

**Finding: R14 was wrong that the English thresholds are missing, and the cause is the parser.** The cached TUM language page holds them (TOEFL iBT 88, IELTS Academic 6.5, PTE Academic 65, Cambridge CAE/CPE grades A-C, or at least 50% of the prior programme taught in English). `ingestion/parser.py` prefers `<main>`, and on that page `html.parser` closes `<main>` before the English accordion, so the cleaned text and every chunk contain only the German section. Consequences: the extractor correctly saw nothing and recorded `english: not_published`, and retrieval cannot answer TUM English questions either. Not fixed here: changing the parser changes the corpus and the Phase 4 retrieval baseline, so it needs its own versioned decision and a re-run of the unchanged retrieval configurations. Other pages with the same pattern are unchecked.

What the rule does meanwhile: the English rule cites the raw cached page. `make eligibility ARGS="--validate"` checks each quote against a verified-record quote, or else against the cached raw HTML text, and only where `data/raw` exists (CI prints "not checked"). The English rule is `reviewed_by: pending` because this interpretation is new. It never reports a failure, only `meets` or `unknown`, because TUM may accept alternative proof under the programme regulations and the new TOEFL 1-6 scale, which are not modelled. The record's `english: not_published` stays unchanged; a Save-path correction is owed.

Possible quiz question: why is a quote that is on the page but missing from the parsed corpus weaker evidence than a verified-record quote, and what does the check do about it?
