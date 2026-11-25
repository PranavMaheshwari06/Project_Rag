# Germany Master's Eligibility Assistant

> **Status: in development.** The data pipeline, retrieval core, requirement extraction with review, the eligibility engine and its API are built. All 13 programmes have verified requirement records: 6 verified by hand field by field, 7 by a second pass over the cited pages (see [Verification](#verification)). The engine has rule files for all 13 programmes, all reviewed by hand, and is evaluated on 40 frozen cases (see [Eligibility evaluation](#eligibility-evaluation)). Retrieval upgrades were tested in an ablation (see [Retrieval ablation](#retrieval-ablation-phase-5)). A small tool-using agent beats one-shot RAG on the 28 multi-hop questions, mostly because one-shot refuses them (see [Agent vs one-shot](#agent-vs-one-shot-rag-phase-7)). Streaming, guardrails, the UI and a public demo come next. See [the project plan](docs/project-plan.md).

Applying for a master's in Germany means checking a dozen official websites: the programme page, uni-assist, APS, the embassy, the blocked-account rules, the city's foreigners' office. Each one says something slightly different, and some of it is only in PDFs. This project reads those official pages for you and answers from them, with a citation and a crawl date on every claim.

A student enters their profile and gets, for each programme:

- **which published requirements they meet, miss, or haven't provided yet**, with margins ("IELTS 6.5 vs 7.0 required, short by 0.5");
- **what is still missing** for each undecided one (a fact, or the university's assessment);
- **the visa, financial-proof and arrival rules that apply** (scholarship matching is planned).

When the sources don't cover a question, it says so instead of guessing.

**What it is not:** an admission predictor. There is no public data on who gets admitted, so any "72% chance" would be invented. It is also not official advice: always confirm with the university or embassy.

## Coverage

- **Country-wide rules** (APS, uni-assist, national visa, blocked account, health insurance, residence permit, job-seeker permit): answered for any German university, from DAAD, uni-assist, APS India, the Federal Foreign Office, BAMF and city service pages.
- **Full eligibility reports** for English-taught MSc programmes in CS, Data Science and AI. 8 universities and 13 programmes: TUM, RWTH Aachen, TU Berlin, Saarland University and TU Dresden (pilot), plus KIT, TU Darmstadt and the University of Stuttgart. More universities are added after launch; that is data work, not code.
- **Anything else** (another university, another country) gets an honest "not covered yet", the general rules, and a link to the official source. Requirements are never invented.

Germany only, on purpose: one country done properly beats three done badly. Every programme record is checked against its official pages before it is used: 6 programmes by hand, field by field, and 7 by a second pass over the cited pages, through the same schema and quote check, with a completed sampled audit. See [Verification](#verification).

## How it works

```mermaid
flowchart LR
    subgraph Offline
        REG[source registry] --> CR[polite crawler]
        CR --> RAW[raw pages + manifest]
        RAW --> ING[parse, clean, chunk]
        ING --> IDX[dense + BM25 indexes]
        ING --> EXT[LLM extraction]
        EXT --> CHK[second-model check]
        CHK --> REV[review<br/>human or second pass]
        REV --> REQ[verified requirements]
    end
    subgraph Per request
        P[student profile] --> RE[rules engine]
        REQ --> RE
        Q[question] --> AG[agent]
        AG --> RET[hybrid retrieval + rerank]
        IDX --> RET
        AG --> RE
        RE --> EXP[cited explanation]
        RET --> EXP
    end
```

**The key design choice: the LLM never decides eligibility.** It extracts requirements from official pages, and every extracted record is checked against its cited official page before it is used. A deterministic rules engine compares the profile with those records. The LLM then only explains the result. So verdicts are reproducible, testable and explainable, and a prompt injection cannot change one.

### Built so far

- **Source registry**: every official URL, labelled by layer (country rules, scholarship, university), journey stage (before applying, visa document, visa and funds, arrival, after graduation), university and programme.
- **Polite crawler**:
  - respects robots.txt and refuses when it can't read it;
  - waits between requests to the same site;
  - follows and records redirects, and caps download size;
  - records a crawl date and a content hash for every page, so later re-crawls can spot changes.
  - Sites that block bots are dropped, not worked around.
- **Parsing**: HTML via BeautifulSoup, PDFs via pdfplumber, with tables kept as markdown. A structure-aware chunker splits on headings and fits the embedding model's 512-token limit. Every chunk carries its source's labels and crawl date, which the retrieval filters use.
- **Hybrid retrieval**, all hand-written (no LangChain or LlamaIndex):
  - dense embeddings (bge-small) and BM25;
  - fused with Reciprocal Rank Fusion;
  - reranked with a cross-encoder (bge-reranker-base).
  - Every result carries its full score trace.
- **Metadata filters** by university, programme, journey stage and layer, with a rule-based detector that reads them from the question. Whether they stay depends on the [retrieval ablation](#retrieval-ablation-phase-5).
- **Grounded answers with a refusal gate**: if the best reranked evidence scores below a threshold, the system declines. Answers cite `[n]` markers mapped back to the source URL. Citation markers that point at no source are stripped.
- **Requirement extraction with review** (`make extract`, `make review`):
  - an LLM reads each programme's official pages and fills a typed `ProgramRequirements` record: degree, credits, grade minimums, English and entrance tests (with the countries they apply to or exempt), German level, APS, deadlines, fees, documents;
  - every field is either "not published" or carries a verbatim quote and the page it came from, and a field whose quote is not in that page is dropped;
  - a second model from a different family cross-checks every field and may suggest a fix, which must pass the same quote check;
  - a local review screen shows each field next to its quote, the full page, automatic warnings and the cross-check verdict. Every field is confirmed against its quote and page before the record is saved as verified: six programmes by hand in this screen, the other seven by a second pass over the cited pages that saves through the same quote check. Verified records are both the product data and the evaluation gold set.
- **Eligibility engine and API** (`make eligibility`, `POST /eligibility/check`): a deterministic engine checks a confirmed profile against cited rule files for all 13 programmes. Each rule returns meets, does not meet, unknown or not published, with a margin and citations, and admission, readiness and finance get separate summaries. A rule still pending review cannot produce a positive headline. `POST /profile/parse` and `make parse-profile` turn pasted text into an unconfirmed draft, keeping only fields backed by a literal span of the text.
- **Evaluation harness**: a 4-way benchmark (vector, BM25, hybrid, hybrid+rerank) on Recall@k, MRR, nDCG and p50/p95 latency, with 95% bootstrap intervals over queries, and extraction accuracy (LLM draft vs verified record). The gold question set has 122 items (requirement 45, country rules 24, confusable programmes 11, multi-hop 28, refusal 9, coverage 5), model-drafted from the verified pages; all are accepted by the maintainer (assisted review, not blinded). `scripts/validate_gold.py` checks every label before `make eval` runs.
- **Serving layer**: `POST /chat/stream` answers by one-shot RAG, hands most refused questions to a six-step agent (`auto`, the default) and streams the process as server-sent events ([contract](docs/production-layer-spec.md)). Public routes are rate-limited per client, a global daily LLM-call cap bounds cost, an answer without a valid citation is refused, prompt-injection cases are tested, and answers to profile-free questions are cached in memory.
- **Pasted sources and feedback**: a pasted page is answered as one passage and the answer is flagged unverified; feedback is stored only with consent and expires ([privacy notice](docs/privacy-notice.md)).
- **Docker**: one API image with the corpus, indexes and models, checked over HTTP by `make docker-smoke`.
- **Observability**: request ids, structured JSON logs with LLM usage per request, and per-stage latency.

### Coming next

UI → free public deployment → MCP server → UI polish. Details and the "done when" check for each phase are in [docs/project-plan.md](docs/project-plan.md).

The [eligibility engine spec](docs/eligibility-engine-spec.md) defines its rules, interfaces and evaluation.

## Verification

Requirement records are the product data, so how each one was verified is recorded in the record itself (`tier` in `data/verified/<slug>.json`):

- **`human` (6 programmes):** every field ticked by hand in the review screen (`make review`), next to its quote, the full page, automatic warnings and the cross-check verdict.
- **`second_pass` (7 programmes: KIT CDS, Saarland CS, TU Darmstadt AIML, TU Dresden CS, TUM DEA, TUM Informatics, Stuttgart CS):** every field re-read against its cited pages in a second pass and saved through the same Save path, which re-runs the schema and quote-in-page check. Not hand-ticked.

Every record went through the same automatic gates first: a field survives only if its verbatim quote is found in the page it cites, and a second model from a different family cross-checks every field (the second-model cross-check). Re-saving a record keeps its tier; promoting `second_pass` to `human` is a deliberate hand edit.

**Sampled audit of the second-pass tier.** The completed audit covers 35 of the original 69 stated fields (seed 4). Strict passes: 29/35 (82.86%; Wilson 95% interval 0.673–0.919); snapshot passes: 32/35 (91.43%; interval 0.776–0.970). Six confirmed findings (rows 12, 16, 20, 22, 28, 32) were corrected through the review Save path; tiers remain unchanged. These are historical pre-correction scores, not a new accuracy estimate. The original values, completed report, provenance and correction evidence are recorded in `data/audit/second_pass_audit.json`. The remaining 34 stated fields and missed fields are unscored.

**Extraction accuracy** (`evaluation/extraction_eval.py`):

| records | programmes | fields | draft unchanged | edited | dropped | added | checker precision | checker recall |
|---|---|---|---|---|---|---|---|---|
| human tier (headline) | 6 | 102 | 0.794 | 18 | 0 | 3 | 0.947 | 0.857 |
| all (second_pass not independent) | 13 | 221 | 0.805 | 35 | 3 | 5 | 0.867 | 0.605 |

How to read it: a field counts as "draft unchanged" only if its status, value, primary citation and any supporting citations are identical after normalizing absent optional defaults between the LLM draft and the verified record, so a corrected citation counts as a correction. On the 6 hand-verified programmes, 79.4% of 102 fields survived verification unchanged. Checker precision is the share of fields the cross-check flagged (wrong, partial or missed) that really changed; checker recall is the share of changed fields it flagged. The headline row uses the human tier only. Caveat: the review screen shows the cross-check verdict, so the checker numbers mean "predicts what a person who could see its verdict changed", and second-pass records were verified with the cross-check's help, so the "all" row is not independent.

## Benchmark

<!-- BENCHMARK:START -->
| config | queries | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| vector | 108 | 0.748 [0.677, 0.818] | 0.860 [0.804, 0.912] | 0.648 [0.578, 0.722] | 0.392 | 0.376 | 22 | 40 |
| bm25 | 108 | 0.693 [0.617, 0.772] | 0.819 [0.755, 0.880] | 0.626 [0.552, 0.699] | 0.364 | 0.344 | 3 | 5 |
| hybrid | 108 | 0.748 [0.676, 0.819] | 0.853 [0.793, 0.906] | 0.704 [0.632, 0.779] | 0.429 | 0.390 | 25 | 44 |
| hybrid_rerank | 108 | 0.801 [0.731, 0.861] | 0.853 [0.793, 0.906] | 0.748 [0.678, 0.813] | 0.462 | 0.404 | 2869 | 3439 |

_108 answerable questions; 122 total items; 614 chunks. Generated 2026-11-12T23:23:52+00:00._

_Brackets: 95% percentile bootstrap interval over queries (2000 resamples, seed 0). Small kinds have wide intervals; read them before comparing configs._

**confusable**

| config | queries | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| vector | 11 | 0.727 [0.455, 1.000] | 0.909 [0.727, 1.000] | 0.577 [0.333, 0.803] | 0.302 | 0.334 | 18 | 23 |
| bm25 | 11 | 0.727 [0.455, 1.000] | 0.909 [0.727, 1.000] | 0.632 [0.385, 0.861] | 0.364 | 0.372 | 2 | 4 |
| hybrid | 11 | 0.818 [0.545, 1.000] | 1.000 [1.000, 1.000] | 0.659 [0.439, 0.864] | 0.380 | 0.380 | 26 | 33 |
| hybrid_rerank | 11 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.768 [0.577, 0.955] | 0.504 | 0.408 | 3047 | 3678 |

**country_rules**

| config | queries | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| vector | 24 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.762 [0.633, 0.882] | 0.548 | 0.535 | 23 | 98 |
| bm25 | 24 | 0.875 [0.708, 1.000] | 0.958 [0.875, 1.000] | 0.705 [0.556, 0.849] | 0.461 | 0.462 | 3 | 4 |
| hybrid | 24 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.845 [0.725, 0.946] | 0.580 | 0.543 | 20 | 27 |
| hybrid_rerank | 24 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.948 [0.865, 1.000] | 0.602 | 0.580 | 2825 | 2932 |

**multi_hop**

| config | queries | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| vector | 28 | 0.494 [0.375, 0.613] | 0.637 [0.530, 0.744] | 0.667 [0.517, 0.807] | 0.388 | 0.331 | 27 | 40 |
| bm25 | 28 | 0.512 [0.393, 0.625] | 0.696 [0.589, 0.804] | 0.660 [0.513, 0.795] | 0.354 | 0.308 | 5 | 6 |
| hybrid | 28 | 0.530 [0.411, 0.643] | 0.649 [0.542, 0.756] | 0.693 [0.541, 0.833] | 0.401 | 0.340 | 27 | 49 |
| hybrid_rerank | 28 | 0.536 [0.429, 0.643] | 0.649 [0.542, 0.756] | 0.654 [0.517, 0.790] | 0.384 | 0.325 | 2841 | 3439 |

**requirement**

| config | queries | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| vector | 45 | 0.778 [0.644, 0.889] | 0.911 [0.822, 0.978] | 0.594 [0.481, 0.703] | 0.333 | 0.330 | 20 | 31 |
| bm25 | 45 | 0.700 [0.556, 0.822] | 0.800 [0.667, 0.911] | 0.561 [0.437, 0.678] | 0.318 | 0.296 | 2 | 4 |
| hybrid | 45 | 0.733 [0.600, 0.867] | 0.867 [0.756, 0.956] | 0.646 [0.517, 0.766] | 0.377 | 0.343 | 27 | 47 |
| hybrid_rerank | 45 | 0.811 [0.689, 0.911] | 0.867 [0.756, 0.956] | 0.695 [0.579, 0.805] | 0.425 | 0.359 | 2917 | 3372 |

| extraction records | programmes | fields | draft unchanged | checker precision | checker recall |
|---|---|---|---|---|---|
| human tier (headline) | 6 | 102 | 0.794 | 0.947 | 0.857 |
| all (second_pass not independent) | 13 | 221 | 0.805 | 0.867 | 0.605 |

_Historical audit: 29/35 strict passes; 32/35 snapshot passes from 69 stated fields (seed 4). These are pre-correction results._

_Refusal calibration: threshold 0.201490405; 5/14 probes refused; 4/108 answerable questions falsely refused. Status: calibrated. Calibration-set results, not held-out evaluation._

| probe kind | probes | refused | missed |
|---|---|---|---|
| refusal | 9 | 4 | 5 |
| coverage | 5 | 1 | 4 |

_Answer quality (hybrid+rerank, extractive): groundedness 1.000, unsupported-claim rate 0.000, refusal rate 0.074 — token-overlap heuristic (not an LLM judge)._
<!-- BENCHMARK:END -->

`make eval` validates the gold set, uses the extractive answer path regardless of API keys, calibrates the score gate, and refreshes these results. Models are warmed before timing; the score sweep reuses retrieval results. The detailed artifact is [refusal_calibration.json](evaluation/results/refusal_calibration.json).

The selected score threshold is `0.20149040532450285`. It refuses 5/14 refusal/coverage probes while falsely refusing 4/108 answerable questions. The constraint is at most 5% false refusals; ties prefer fewer false refusals, then a lower threshold. These are calibration-set results, not held-out estimates. Actual answer refusals are reported separately in the calibration artifact.

### Refusal with the LLM on

The calibration above uses the extractive path, so it measures only the score gate. `make eval-llm-refusal` runs the real one-shot path (gate, then `gemini-3.8-flash`) on the 94 non-multi-hop gold items and records who refused: the gate, the model, or the citation check. Answer correctness is not judged. Result file: [llm_refusal.json](evaluation/results/llm_refusal.json).

| items | n | answered | refused by gate | refused by model |
|---|---|---|---|---|
| answerable (requirement, country rules, confusable) | 80 | 66 | 4 | 10 |
| refusal and coverage probes | 14 | 1 | 5 | 8 |

**Current prompt (Phase 8):** 14 of 80 answerable questions are refused (17.5%, 95% bootstrap interval [10.0%, 26.3%]), down from 23 of 80 (28.7%, [18.8%, 38.8%]) before the change. The intervals overlap, so the evidence is the paired comparison: 10 questions moved from refused to answered and none the other way (exact sign test, p = 0.002). By kind: requirement 6 of 45, country rules 2 of 24, confusable 6 of 11. The change came from reading the 19 earlier model refusals against their evidence: in 18 the answer was not in the four passages the model saw (9 times the right page was missing, 9 times the right page was there but not the passage with the fact), and once the model refused a question it could half answer. So the prompt now allows a partial answer that says what the evidence does not cover, treats university-wide and city pages as applying to every programme there, and forbids answering from another university's or programme's page. A partial answer is counted as answered: of the 10 newly answered questions, none states a wrong fact, but 2 only say what is missing and 1 misses the key point (RWTH CS needs German too). Most remaining refusals are retrieval misses, which is what `auto` mode (below) goes after.

One probe is now answered by this metric (d25, "what are my chances with a 7.8 CGPA?"): the model says the chances cannot be determined and lists the published requirements instead, which matches the product rule (never an admission probability) but is not the refusal text. We count it as handled: the gold item's own expected behaviour is "only compare the profile with the published requirements", and forcing the refusal text would turn a useful cited answer into a dead end. The probe bar is therefore 13 refused plus d25 giving no chance or probability. Two runs of the new prompt used 170 LLM calls, about 0.43 USD; the first wording, without the university-wide clause, refused 21 of 80 and lost 4 good answers, which is why the clause exists.

**`auto` mode, the default of `POST /chat/stream`.** One-shot answers first; if it refuses, the agent gets one try ([when it escalates](docs/production-layer-spec.md#when-auto-escalates)). Measured on top of the same 94 one-shot replies (`make eval-llm-refusal ARGS="--mode auto"`, result file [auto_refusal.json](evaluation/results/auto_refusal.json)):

| | one-shot | `auto` |
|---|---|---|
| answerable questions refused, as the script counts | 14 of 80 (17.5%, [10.0%, 26.3%]) | 0 of 80 |
| of those 14, replies that give the fact asked for | - | 12 of 14 |
| probes handled (13 refused, d25 answered without estimating a chance) | 14 of 14 | 14 of 14 |
| LLM calls per question | 0.90 | 1.65 |

An escalated question waits another 13 s at the median (29 s at the 95th percentile).

Read the 0 with care. The script counts any cited reply as answered, and two of the recovered replies miss the point. Asked whether part-time students of TUM Informatics pay the full fee, and whether KIT Computational and Data Science requires a bachelor thesis, the agent says its evidence does not settle it, although both programme pages do (for the thesis it also says none is listed among the requirements). So 2 of 80 are still not answered, and those two are worse than a refusal. An earlier run of the same measurement, before the agent prompt got one-shot's scope and partial-answer rules, refused both and recovered the same other 12.

Other limits. `auto` can only lower the refusal count, so no significance test is given. The score cut for gate refusals was chosen on these same items and keeps only 3 of the 14 probes away from the agent; without the gate path the agent gets 8 of the 10 model refusals right, leaving 6 of 80 unanswered. The 10 probes that reached the agent were refused in both runs, which does not prove that a question about an uncovered university is never answered from another one's page. A refused probe gets a bare refusal, not yet a pointer to the right official source. Correctness is not scored by machine: a second model read the 14 recovered replies against the gold facts and pages (one of the 12 omits the new TOEFL scale its page also gives); they are not yet checked by hand. The reported run used 70 LLM calls.

### Retrieval ablation (Phase 5)

`make ablation` runs hybrid+rerank three ways on the same gold set: no filter (baseline), filters taken from each question's gold metadata (an upper bound no deployed system has) and the rule-based detector in `retrieval/filters.py` (what `/answer` could do). A filter only counts as an improvement if the 95% paired bootstrap interval of its per-question MRR gain lies above zero, and it must not change refusal behaviour. Result file: [ablation.json](evaluation/results/ablation.json).

<!-- ABLATION:START -->
| questions | arm | n | MRR [95% CI] | MRR gain vs baseline [95% CI] | Recall@5 | p50 ms |
|---|---|---|---|---|---|---|
| all | baseline | 108 | 0.748 [0.678, 0.813] | — | 0.801 | 2541 |
| all | oracle_filter | 108 | 0.785 [0.720, 0.849] | +0.037 [+0.001, +0.074] **win** | 0.856 | 2528 |
| all | detected_filter | 108 | 0.785 [0.719, 0.849] | +0.037 [+0.001, +0.074] **win** | 0.867 | 2507 |
| human_reviewed | baseline | 108 | 0.748 [0.678, 0.813] | — | 0.801 | 2541 |
| human_reviewed | oracle_filter | 108 | 0.785 [0.720, 0.849] | +0.037 [+0.001, +0.074] **win** | 0.856 | 2528 |
| human_reviewed | detected_filter | 108 | 0.785 [0.719, 0.849] | +0.037 [+0.001, +0.074] **win** | 0.867 | 2507 |
| confusable | baseline | 11 | 0.768 [0.577, 0.955] | — | 1.000 | 2592 |
| confusable | oracle_filter | 11 | 0.814 [0.623, 1.000] | +0.045 [+0.000, +0.136] | 1.000 | 2520 |
| confusable | detected_filter | 11 | 0.814 [0.623, 1.000] | +0.045 [+0.000, +0.136] | 1.000 | 2560 |
| country_rules | baseline | 24 | 0.948 [0.865, 1.000] | — | 1.000 | 2518 |
| country_rules | oracle_filter | 24 | 0.951 [0.875, 1.000] | +0.003 [+0.000, +0.010] | 1.000 | 2517 |
| country_rules | detected_filter | 24 | 0.951 [0.875, 1.000] | +0.003 [+0.000, +0.010] | 1.000 | 2506 |
| multi_hop | baseline | 28 | 0.654 [0.517, 0.790] | — | 0.536 | 2527 |
| multi_hop | oracle_filter | 28 | 0.689 [0.558, 0.815] | +0.035 [-0.026, +0.100] | 0.589 | 2531 |
| multi_hop | detected_filter | 28 | 0.690 [0.561, 0.816] | +0.035 [-0.026, +0.100] | 0.631 | 2494 |
| requirement | baseline | 45 | 0.695 [0.579, 0.805] | — | 0.811 | 2551 |
| requirement | oracle_filter | 45 | 0.749 [0.643, 0.847] | +0.054 [-0.022, +0.130] | 0.911 | 2534 |
| requirement | detected_filter | 45 | 0.749 [0.643, 0.847] | +0.054 [-0.022, +0.130] | 0.911 | 2546 |

| arm | refusal probes refused | answerable questions refused |
|---|---|---|
| baseline | 5/14 | 4/108 |
| oracle_filter | 5/14 | 6/108 |
| detected_filter | 5/14 | 6/108 |
<!-- ABLATION:END -->

**Result: filters stay off in `/answer`.** The detector matches the oracle upper bound and lifts MRR by +0.037 [+0.001, +0.074] on all 108 answerable questions, which are now all human-reviewed (re-run 2026-11-16), so the gain is unlikely to be noise, though its lower edge is close to zero. It fails the second condition: false refusals rise from 4 to 6 of 108 (5.6%, above the 5% limit), because the refusal threshold was calibrated without filters. Revisit only together with a recalibration of the threshold on filtered scores.

### Agent vs one-shot RAG (Phase 7)

`make compare-agent` runs both arms on the 28 human-reviewed multi-hop questions: one-shot RAG (hybrid+rerank, one LLM call) and the agent (tool loop, at most six calls, read-only tools). Scoring is deterministic, no LLM judge: `doc_recall` is the share of a question's relevant pages that the answer cites; `fact_recall` is the share of the numbers in the reviewed answer found in the answer. A refusal or an uncited answer scores 0. The headline is the paired difference with a 95% bootstrap interval; above zero is a win. Both arms used `gemini-3.8-flash` for every call. Result files: [agent_comparison.json](evaluation/results/agent_comparison.json), [agent_comparison.jsonl](evaluation/results/agent_comparison.jsonl).

| metric | n | agent | one-shot | agent minus one-shot [95% CI] |
|---|---|---|---|---|
| doc_recall | 28 | 0.786 | 0.125 | +0.661 [+0.482, +0.821] **win** |
| fact_recall | 23 | 0.813 | 0.116 | +0.697 [+0.551, +0.848] **win** |

| arm | refused | LLM calls per question | mean latency |
|---|---|---|---|
| one-shot | 22/28 | 1.0 | 16 s |
| agent | 4/28 | 4.4 | 44 s |

**Result: the agent beats one-shot on multi-hop questions, but most of the gap is refusals.** One-shot refuses 22 of 28, but not at the score gate: all 28 questions pass it (lowest top score 0.216 against the 0.20 threshold). The model itself replies "not enough evidence", mostly because its single retrieval did not bring in both pages: for 18 of the 22 refused questions the top 5 passages miss at least one relevant page (mean recall@5 0.50, against 0.67 for the 6 it answered). On those 6 questions the gap is small: `doc_recall` 0.75 (agent) vs 0.58, `fact_recall` 0.90 vs 0.53, too few questions for an interval. The agent costs about four times the calls and three times the latency, and it still refuses 4 of 28 (2 refusals, 1 unparseable reply, 1 uncited). The reported run used 152 LLM calls and about 0.38 USD at the published Flash price. It is the second run: the first, made before the loop learned to ignore stray text after a JSON reply (which had wasted calls and ended some questions as unparseable), gave `doc_recall` 0.589 vs 0.143 and 9 of 28 agent refusals. The interval is above zero in both runs, but the model is not deterministic even at temperature 0, so the point estimates move between runs. Both runs predate two rules later added to the agent prompt in Phase 8 (stay with the university and programme asked about; answer in part and say what is missing), and they have not been repeated since.

## Run it locally

Needs [uv](https://docs.astral.sh/uv/) and Python 3.12. `crawl` fills the git-ignored `data/raw/`; `ingest`, `index`, `review` and `eval` need it, while `test`, `eligibility` and `--validate` work on a fresh clone. The first run downloads two models from Hugging Face (bge-small ~130MB, bge-reranker-base ~1.1GB). After that, everything except `make crawl` runs offline.

```bash
make install    # creates .venv and installs the pinned versions from requirements.lock
make crawl      # fetch every registry source into data/raw/ (the only network step; cached pages are skipped)
make ingest     # parse, clean and chunk -> data/processed/chunks.jsonl
make index      # dense (NumPy) + BM25 indexes
make extract    # LLM requirement drafts -> data/extracted/ (needs GEMINI_API_KEY)
make review     # review screen on http://127.0.0.1:8001 -> data/verified/
make test       # pytest (offline, uses its own fixture corpus)
make eval       # validate, benchmark, calibrate, and persist the selected threshold
make run        # API on :8000
make eligibility ARGS="--profile data/eligibility/examples/synthetic_kit_cs.json --programme kit-m-sc-computer-science --as-of 2027-05-01 --intake winter --starting-year 2027"
                # eligibility report for one profile and intake: admission, readiness and finance summaries, one line per rule
make eligibility ARGS="--validate"                # rule files bound to their records, quotes in the record; visa funds quotes against the cached page
make eligibility ARGS="--validate --check-cache"  # also requires the cached page for quotes the record lacks (needs data/raw)
make parse-profile ARGS="--input draft.txt"  # pasted text -> unconfirmed draft profile (needs GEMINI_API_KEY; synthetic text only)
make eval-eligibility  # validate evaluation/datasets/eligibility_cases.jsonl, run it, write evaluation/results/eligibility_baseline.json
                       # (exits 1 if the cases file is missing or invalid)
```

Frontend (Node 18+):

```bash
cd frontend
npm install
npm run dev     # :5173, talks to the API on :8000
```

No API key is needed, except for `POST /profile/parse` and `make parse-profile`. Without one, answers come from an extractive fallback, which stitches together quoted sentences from the cited evidence. For the LLM path (Gemini, free tier) and `make extract`, copy `.env.example` to `.env` and set `GEMINI_API_KEY`. The free tier allows about 20 requests a day per model; `make extract` skips finished programmes, so re-running it the next day fills the gaps. All tunables live in `config/settings.yaml`.

`requirements.lock` pins every package for Linux with CPU-only torch, the same setup CI and Docker use. On another platform, or without Make: `uv venv --python 3.12`, then `uv pip install -e '.[dev]'`.

Docker: after `make ingest index` (the corpus is not in git), `make docker-smoke` builds the API image, runs it without a key and checks over HTTP: readiness, a frozen eligibility case, a cited answer, the event stream, an injection string, feedback and the request limit. `docker compose up --build` (`make up`) runs the API and the UI on localhost. The image holds the code, verified records, rules, chunks, indexes and both retrieval models, and runs one worker as an unprivileged user. Public hosting is not verified yet.

## Eligibility evaluation

`make eval-eligibility` runs the rules engine on 40 profiles whose expected verdicts were written from the cited official pages before any engine run (5 by the maintainer, 35 assisted; 17 are independent observations, the rest are variants). Result in [eligibility_baseline.json](evaluation/results/eligibility_baseline.json): 40/40 headline verdicts and 213/213 per-criterion verdicts agree, with 0 false-positive "meets" headlines. The engine decided 211 of 334 applicable criteria (63%); the rest are `unknown` because they need a university assessment (74), a fact the profile did not give (48) or a funds route with no published comparison (1), by design. Application deadlines are encoded for 12 of 13 programmes (TU Berlin publishes none on its registry pages); those added on 2026-11-12 are awaiting human review and cannot yet mark readiness as complete.

This measures agreement with the sources as read by the maintainer, not an independent audit, and it is not an admission probability.

## Honest limitations (current)

- **Free-tier LLM quota.** About 20 requests a day per model, so extraction of many programmes takes more than one day and the hosted chat will need caching.
- **Small corpus, single node.** In-memory BM25 and brute-force cosine search. Fine for thousands of chunks, not millions.
- **Small, assisted gold set.** All 122 items are model-authored and were accepted by the maintainer (assisted review, not blinded). Labels still have known source overlap; this is not an independent human-written evaluation. Refusal results use the calibration set itself.
- **Score-only refusal remains weak.** The selected threshold misses 9 of 14 refusal/coverage probes while falsely refusing 4 of 108 answerable questions. Coverage checks need more than a relevance score; calibration is a measured baseline, not a solved coverage policy.
- **Seven of 13 programme records are not hand-verified.** They were verified by a second pass over the cited pages and are labelled `second_pass`; a completed 35-field sample found six strict failures, now corrected; unsampled fields remain unscored.
- **Official pages change.** Every answer shows its crawl date. A weekly re-crawl with human review of changed pages comes with deployment.
- **The extractive fallback is quotes, not prose.** It is grounded by construction but not fluent.
- **Answer groundedness is a token-overlap heuristic**, labelled as such. It is not an LLM judge.

## Privacy

The server keeps no accounts and stores no profile, question or pasted text. The one thing a user can make it write down is a feedback note (`POST /feedback`, with consent, kept 90 days). Questions, pasted texts and `POST /profile/parse` input go to the configured LLM provider; a profile used in the chat does not, only the rules engine's result for each requirement. Answers cite official public pages; an answer that also used the student's own pasted text is flagged as unverified. The Gemini free tier may use prompts to improve its products, so use synthetic text there. Details: [privacy notice](docs/privacy-notice.md).
