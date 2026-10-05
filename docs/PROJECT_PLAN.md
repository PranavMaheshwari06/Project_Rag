# Project plan: study-abroad admissions and eligibility assistant

Status: living document. Last updated 2026-10-05. Phase 1 (clean base) is done. Next: Phase 2.

This repository started as EngineerDoc AI, a hybrid RAG service over technical documentation. It is being turned into a study-abroad assistant for students applying to Germany, the UK and the US. The hand-written retrieval core is kept; the corpus, extraction, eligibility logic, agent, UI and deployment are new. `DECISIONS.md` records the reasoning behind each major choice.

## 1. The product

A student enters a profile. For a shortlist of programmes the system shows:

- which published requirements they **meet, miss, or have not provided**, each with a citation;
- what to fix;
- the visa and financial-proof rules and the scholarships that apply.

The student can also chat freely. Every claim links to an official page and shows its crawl date. When a source does not cover a question, the system says so.

## 2. Key decisions

### 2.1 Why Germany, the UK and the US
This is a scope decision, stated once on the coverage page and in the README. The reason is engineering, not "these countries are best":

- They are among the largest destinations for international students.
- They are three structurally different admissions systems:
  - **Germany** is rule-based: uni-assist, APS for some nationalities, a blocked account, grade conversion.
  - **The UK** is grade-equivalency tables per country.
  - **The US** is holistic, so only published minimums apply.

Handling three different systems shows the design generalises. A fourth country means adding sources and a schema mapping. A question about an uncovered country gets a coverage-aware refusal ("I currently cover DE/UK/US only") plus the official portal link. That behaviour is evaluated too.

### 2.2 Eligibility report, not an admission probability
- **Not offered: a probability of admission.** There is no public admissions-outcome data, and UK/US selection is holistic and changes yearly. A number like "72% chance" would be invented.
- **Offered: an eligibility and gap report against published requirements.**
  1. **LLM structured extraction.** Each programme page becomes a `ProgramRequirements` record: minimum grade and scale, required degree or field, ECTS/credit prerequisites, IELTS/TOEFL/Duolingo minimums, GRE/GMAT, APS, work experience, deadlines, fees, documents. Each field cites its source span.
  2. **Human verification.** The extracted JSON is reviewed by hand. The verified records are both the product data and the gold evaluation set.
  3. **Deterministic rules engine.** It compares the profile with the requirements. Each requirement returns `meets`, `does_not_meet`, `unknown` (missing info) or `not_published`. The LLM never decides eligibility; it only extracts and explains.
  4. **Deterministic tools** for grade conversion (for example the German modified Bavarian formula) and test-score equivalence where officially published.
  5. **Competitiveness is qualitative and cited.** If a page says "typically admitted students have…", we quote it.
- **Numbers in the report, with no invented weights:**
  - A count: "6 of 8 published requirements met · 1 not met · 1 missing info".
  - A margin on every numeric criterion: "IELTS 6.5 vs 7.0 required → short by 0.5".
  - A hard/soft flag per requirement ("must" vs "recommended"). One unmet hard requirement makes the headline "Not eligible as published", whatever the count.
  - No weighted single score.
- **Scope:** master's programmes in CS, Data Science and AI. Requirements are per programme, so a fixed field keeps the workload bounded. Adding fields later is data work, not code.

### 2.3 The whole journey, not only admission
Visa rules are mostly per country but connect to the university at specific points. Each stage comes from official sources.

| Stage | Germany | UK | US | University-specific link |
|---|---|---|---|---|
| Before applying | APS (some nationalities), uni-assist, language tests | UCAS / direct application, ATAS for some STEM courses | Application, test policies | Programme requirements |
| Admission → visa document | Admission letter | CAS issued by the university | I-20 issued by the university | The university issues the document the visa depends on |
| Visa and funds | National D visa, blocked account, health insurance | Student visa, maintenance funds (London vs outside) | F-1, SEVIS fee, interview, funds = university's cost of attendance | Location and university change the money needed |
| Arrival and during study | City registration, residence permit, work-hour limits | BRP/eVisa, work-hour limits | On-campus work rules, maintaining status | City of the university |
| After graduation | Post-study job-seeker permit | Graduate Route | OPT / STEM OPT | Some depend on the programme |

- The **funds check** is a deterministic rule: the profile budget is compared with the required financial proof for that country, city and university, with a margin and a citation.
- **Extensions and status changes** are answered as cited official procedure only, never as personal advice.
- **City-level offices** (for example foreigners' offices) are covered only for the cities of covered universities.

### 2.4 Profiles: no accounts, privacy by design
- The profile form covers nationality, degree, grade and scale, field, credits, language tests, GRE, work experience, budget, target countries and intake.
- A "paste your CV or profile" box fills the form via structured output. The user confirms or edits before anything is checked.
- The profile lives only in the browser (localStorage) and is sent with each request. The server is stateless: no auth, no database of personal data, no profile fields in logs. Profiles can be exported and imported as JSON.

### 2.5 "Show the whole process" view
Each request streams its steps (SSE) into a process panel with a "simple / show the work" toggle:

1. **Input understood**: each extracted profile field next to the phrase it came from, with a confidence score; low-confidence fields are flagged.
2. **Sources retrieved**: documents found, crawl dates, retrieval scores (the existing score trace on `RetrievedChunk`).
3. **Rules checked**: per criterion, your value → required value → verdict → citation.
4. **Explanation**: written answer pointing back to the rows above.

The form skips step 1; a pasted profile runs extraction first; a chat question goes through the agent's tool calls, each shown as a step.

### 2.6 User-typed text
Three kinds of user text, never mixed:

1. **Extra facts about themselves**: extracted into profile fields, confirmed, then checked.
2. **A source for a programme we do not cover: pasted text only, no URL fetching.** Used for that request only, never added to the corpus or cached, labelled "user-provided, not verified", and treated strictly as data (prompt-injection guardrails apply). This removes the SSRF surface and any dynamic scraper.
3. **"This answer is wrong" feedback**: stored only with explicit consent and without the profile (answer id, source id, note). It goes into a review queue; the maintainer checks it against the official page and fixes the verified data or the gold set.

## 3. LLM provider and deployment

### 3.1 LLM
The project uses the **Gemini free tier** (Google AI Studio key, no billing) through Gemini's OpenAI-compatible endpoint. `generation/llm_client.py` is the only module that touches the SDK, so the provider stays swappable. A `base_url` setting is added in Phase 3.

- The key goes in `.env` as `GEMINI_API_KEY`. It is never committed or pasted into chat.
- Free-tier rate limits and model names change; re-check them at build and deploy time rather than hard-coding assumptions.
- Free-tier prompts may be used by the provider to improve its products. Public university pages are fine. **Do not send real personal profiles through it during development**, and say so in the privacy notice for the hosted demo.
- Cost control is request-based: a per-IP daily cap and a global daily request cap. When the cap is hit, the UI shows "demo quota reached".
- A small model handles extraction, routing and most answers; a stronger one is used only for hard multi-hop questions and the offline judge. Answers are cached.
- Extraction and the judge run once locally and results are committed as JSON. Deploys never re-run them.

### 3.2 Hosting (free)

| Part | Option | Notes |
|---|---|---|
| Frontend | Cloudflare Pages | Static hosting with a free subdomain. |
| Backend + models | Hugging Face Space (Docker, free CPU tier) | Sleeps when idle, so the first request is slow; the README says so. |
| Vector store | In-process NumPy (or Qdrant local mode) | A few thousand chunks fit in memory. |
| LLM | Gemini free tier | See 3.1. |

The reranker size is an evaluation decision: bge-reranker-base is measured against a smaller cross-encoder, partly for cold-start time. CORS is currently hard-coded to `localhost:5173` and must become configurable before deployment.

### 3.3 After launch
The app runs on the hosts and does not need a laptop. Updates are automated with one deliberate human step:

1. A weekly scheduled GitHub Action re-crawls every source and detects changes by content hash.
2. For changed pages it re-runs extraction and opens a pull request showing the page diff and changed fields.
3. The maintainer reviews and merges (about 10–20 minutes a week). Publishing an extracted visa or fee change without a human check is how a trusted tool starts giving wrong answers.
4. The merge triggers CI (tests, evaluation-regression gate, index rebuild) and, if green, auto-deploys.
5. Answers built on pages that failed to re-crawl or are older than N days are shown as "may be outdated".
6. Dependabot opens dependency PRs and a free uptime check pings the backend.

## 4. Security, privacy and EU considerations
Engineering due diligence, not legal advice; have a lawyer review it before any commercial use.

- **Data minimisation:** profiles stay in the browser; the server is stateless.
- **IP addresses are personal data under GDPR.** Rate limiting keeps hashed IPs in memory only (24 h or less), never on disk. Logs carry a request id, latency and usage, not IPs or profile fields.
- **No tracking cookies or analytics.** localStorage holds only what the user entered. A plain-language privacy notice page is included.
- **Third-party processors are disclosed:** request content is sent to the LLM provider; the hosting region is stated.
- **Feedback storage** is opt-in, contains no profile, can be deleted on request, and has a retention limit.
- **EU AI Act:** AI systems that determine access or admission to education are high-risk. This tool is a self-service information aid and makes no decision for any institution; the UI and README say so. Transparency duties are met: clearly labelled as AI, answers cite sources, and every report carries a "not official advice; confirm with the university or embassy" note.
- **Application security:** secrets only in host environment variables, secret scanning and dependency audit in CI, CORS locked to the frontend domain, input size limits, agent tools read-only (so injected text cannot trigger actions), PDF parsing size and page limits.
- **Content and licensing:** respect robots.txt and site terms (gov.uk content is under the Open Government Licence). Text is stored for retrieval but only short excerpts are shown, always with a link to the source.

## 5. Scope: vertical slice first

**Milestone A (MVP, deployed): Germany only**, country rules and journey stages, DAAD and uni-assist, through all phases.

- **Universities (17):** one per federal state plus Passau and Braunschweig: KIT, TUM, Passau, TU Berlin, Potsdam/HPI, Bremen, TU Hamburg, TU Darmstadt, TU Braunschweig, Rostock, RWTH Aachen, RPTU Kaiserslautern-Landau, Saarland, TU Dresden, OVGU Magdeburg, Kiel, TU Ilmenau.
- **Programmes (~25):** English-taught MSc in CS, Data Science or AI. Flag any university with none.
- **Rollout:** build and verify the pipeline on 5 universities (TUM, RWTH, TU Berlin, Saarland, TU Dresden), then add the rest in batches. After that, adding a university is data work.
- **Coverage tiers:**
  1. Country-wide rules answer for any German university.
  2. The full eligibility report covers only verified programmes.
  3. An uncovered programme gets a coverage notice, the tier-1 rules, a DAAD database link and the paste-text unverified check.
- **No fragile scrapers.** Fetch registry URLs, cache raw HTML/PDF, convert to text, run LLM extraction over the text. Tables use pdfplumber. No per-site CSS selectors.

**Milestone B:** add the UK (tests whether the schema and rules generalise).
**Milestone C:** add the US and bring each country to 10–12 universities.

**Demo reliability:** the frontend pings `/health` on load and shows an honest wake-up status. 2–3 precomputed demo profiles ship as static JSON so a full report renders even when the backend is asleep or the quota is hit.

**UI:** Tailwind + shadcn/ui replace the plain CSS. Wireframes come before the UI phase; the process panel is the centrepiece; basic accessibility checks are kept.

## 6. Target structure

```
sources/registry.yaml   every source URL + country, layer (rules|scholarship|university), uni, programme
ingestion/              crawler (robots.txt, cache, crawl date, change detection), HTML+PDF parsing,
                        chunker (keep, add table-aware), metadata on every chunk
extraction/             LLM -> ProgramRequirements / Scholarship (pydantic), verified JSON committed
eligibility/            profile schema, rules engine, grade conversion (pure Python, fully unit-tested)
retrieval/              keep hybrid core; add metadata filters, query rewrite, parent-child
agent/                  hand-rolled tool-use loop, step budget, refusal
mcp_server/             MCP server exposing the same tools (search_sources, get_requirements,
                        check_eligibility, convert_grade, find_scholarships)
generation/             LLM client (OpenAI-compatible), structured answers, citations, guardrails
evaluation/             retrieval gold, extraction accuracy, eligibility verdict accuracy on synthetic
                        profiles, refusal/coverage probes, judge-based faithfulness, cost/latency
api/                    SSE streaming, rate limit + request cap, cache, tracing, usage per request
frontend/               profile form + paste-to-fill, eligibility report, chat with sources, coverage
                        page, evaluation dashboard
ops/                    Dockerfile, docker-compose (local), GitHub Actions (lint, tests, build, eval gate),
                        deploy to HF Spaces + Cloudflare Pages
```

## 7. Phases

Each phase ends runnable and measured. The first three columns are the work; the last two are the manual task and the concept to learn.

| # | Phase | What gets built | Manual task | Concepts |
|---|---|---|---|---|
| 1 | Clean base | Done: reranker normalisation, test isolation, `vite-env.d.ts`, CI workflow, stale docs removed | — | — |
| 2 | Sources and ingestion | Source registry checked against live sites; polite crawler (robots.txt, cache, crawl date); HTML/PDF parsing; chunks with metadata; journey-stage sources. 5 universities first, then the rest | Review the source list, confirm programmes, decide robots.txt / terms-of-use issues (~30 min) | Crawling ethics, parsing, chunking, provenance |
| 3 | Extraction | Requirement schemas, LLM extraction, simple review screen showing each field next to its source text; `base_url` setting for the LLM client | **Verify every extracted record** (~3–5 h) | Structured outputs, schema design, field-level accuracy |
| 4 | Eval baseline | ~150 draft gold questions, ~40 synthetic profiles, first benchmark numbers with the four existing retrieval modes | Review/fix drafts, write ~20 questions (~2–3 h) | Recall, MRR, nDCG; gold sets; judge bias |
| 5 | Retrieval upgrades | Metadata filters, query rewriting, parent-child retrieval, ablation table; each kept only if the benchmark improves | Read results and decide what stays | Ablation method |
| 6 | Eligibility engine | Profile schema, rules engine, grade conversion, funds check, hard/soft flags, margins, paste-to-fill | Write 5 realistic anonymised profiles and check verdicts | Deterministic logic vs LLM |
| 7 | Agent and MCP | Tool-use loop; MCP server with the same tools; agent vs one-shot RAG compared on multi-hop questions | Connect the server to an MCP client and try to break it | Agent loops, tool design, MCP |
| 8 | Production layer | SSE streaming, guardrails, caching, rate and request caps, tracing, user-source path, feedback queue, privacy notice, Docker, CI eval gate | Run the Docker setup and attempt prompt injections | LLMOps, security, containers |
| 9 | UI | Wireframes first, then profile form, report, process panel, chat, coverage page, dashboard | Approve wireframes, give usability feedback | Streaming UIs, UX for AI |
| 10 | Deploy and showcase | HF Space and Cloudflare Pages config, weekly re-crawl workflow, README with real numbers, architecture diagram, `LEARNING.md` | Create accounts, add secrets, press deploy | Deployment, CI/CD, operations |

**One-time setup:** GitHub repo (done); Gemini API key in `.env` before Phase 3; Docker Desktop with WSL integration (done); MCP client installed before Phase 7; Hugging Face and Cloudflare accounts before Phase 10; product name chosen before Phase 9.

### The loop for every phase
1. **Kick off.** "Start Phase N" → a short brief: what gets built, what the maintainer must do, what "done" means.
2. **Build** in small steps, each leaving a test or check behind.
3. **Hands-on task** (the manual column above).
4. **Run it yourself** with the commands provided.
5. **Explain.** "Explain Phase N" → a walkthrough of how it works and why.
6. **Checkpoint.** Write the phase's `DECISIONS.md` entry in your own words, then "Quiz me on Phase N": 3–5 interview-style questions with honest feedback.
7. **Commit.** "Commit Phase N": one branch and one PR per phase.

Other commands: "Continue Phase N, step X", "Pause, explain why X", "Status?", "I disagree with X because Y". New session: "Continue the study-abroad project, Phase N".

## 8. Carried over from the earlier review
Items from the October review that still apply and are folded into the phases above:

- Reranker: explicit activation (done in Phase 1); recalibrate the refusal threshold with real scores (Phases 4–5).
- Cleaner: do not strip comments or collapse blank lines inside fenced code (Phase 2).
- Chunking: respect model token limits (bge-small: 512 tokens); keep parent context for display (Phases 2 and 5).
- Answer contract: reject or repair empty, uncited or invalid-citation LLM output; add refusal reasons (Phases 3 and 8).
- Evaluation: validate gold labels, add refusal probes, warm models before timing, report sample counts (Phase 4).
- Serving: readiness vs liveness on `/health`; rate limits and request deadlines; `/ingest` and `/evaluate` become admin or job-only (Phase 8).
- Tests: no test may write real data, README or benchmark files, or call a paid provider (Phase 1 started this).
- Deployment: same-origin or configurable API base and CORS; benchmark published as a build artifact, not an API write (Phase 10).

## 9. Skills covered

| Area | What gets built |
|---|---|
| Data engineering | Crawling, PDF/HTML/tables, provenance, freshness |
| Retrieval and RAG | Hybrid search, reranking, filters, rewriting, citations |
| LLM engineering | Structured extraction, schema validation, model routing |
| Agentic AI and MCP | Tool-use loop, MCP server |
| Evaluation | Gold sets, judge, ablations, CI gate |
| LLMOps | Tracing, usage, caching, caps |
| Backend and DevOps | FastAPI, Docker, CI/CD, free deployment |
| Frontend | React UI |
| Responsible AI | No-advice framing, stateless privacy, honest limits |

## 10. Constraints
- No LangChain or LlamaIndex; the LLM SDK is used directly through the thin client.
- Settings stay in `config/settings.yaml`.
- Each feature leaves a runnable check or test behind.
- The LLM never makes the eligibility decision.

## 11. Verification (end state)
- `make test` and CI are green.
- `make ingest index eval` produces non-PENDING numbers that the dashboard renders.
- Extraction accuracy and eligibility-verdict accuracy are reported against the verified gold data.
- The MCP server works from an MCP client.
- The deployed URL serves a streamed, cited answer and an eligibility report for a pasted profile.

## 12. Open items
- Product name: to be chosen before Phase 9.
