# Phase 6 implementation plan: cited eligibility and gap reports

Status (2026-11-06): Steps 0-4 are done and merged: the inventory, the profile/rule/report types, the deterministic primitives, rule files for all 13 programmes, and the API with paste-to-fill. Report summaries per area, the `--check-cache` validation flag, an explicit "no GRE/GATE" answer, the evaluation harness, deadline and test-age checks, a cited visa funds rule, no-minimum-published info rules and a reported university assessment (TU Berlin and KIT CDS) are merged too. 19 rules are still pending review. The five human-authored cases are not frozen, so no evaluation has run. This specification follows [the project roadmap](PROJECT_PLAN.md).

## 1. Purpose and boundaries

Deliver a deterministic report that compares a confirmed student profile with published requirements for the existing **13 programmes at eight German universities**. Show the requirement, entered fact, comparison, numeric margin, citation, and next action. Keep academic eligibility, application readiness, and financial checks distinguishable.

For students, the value is knowing what matches, what is missing, what needs university review, and what to do next.

Included: profile schema; reviewed machine-readable rules; grade conversion; language/credit/test/APS checks; conditional routes and exemptions; deadline/document readiness; cited funds comparison; text-to-profile extraction with confirmation; API and CLI; approximately 40 synthetic evaluation cases; five human-authored cases; documentation and CI.

Later phases retain their assigned work: retrieval experiments in Phase 5, agent orchestration in Phase 7, streaming/serving controls and generated explanations in Phase 8, the full browser form/report/localStorage experience in Phase 9, deployment in Phase 10, MCP in Phase 11, and visual polish in Phase 12. Phase 6 exposes reusable functions for those phases. It does not produce admission probabilities or infer university decisions.

## 2. What Phase 4 established, and why Phase 6 comes next

Phase 4 recorded verification tiers, the 35-of-69 sampled audit, all six corrections, and human acceptance of the 104 model-authored gold questions. It added source/quote validation, compatible schema additions, and the two missing sources. The baseline covers 74 sources and 600 chunks with zero embedding truncations.

| Evidence | Phase 4 result |
|---|---|
| Historical audit | 29/35 strict passes; 32/35 snapshot passes, preserved before corrections |
| Human-tier draft unchanged | 0.794 over 102 fields in six programmes |
| Human-tier checker precision / recall | 0.947 / 0.857; reviewer could see checker verdicts |
| Hybrid + rerank retrieval | Recall@5 0.872; Recall@10 0.906; MRR 0.774 |
| Rerank CPU latency | p50 5,059 ms; p95 6,251 ms on the recorded run |
| Refusal calibration | 4/14 probes caught; 3/90 answerable questions falsely refused |
| Verification | 68 tests, lint, frontend production build, gold validation, and all 13 record/citation checks passed |

These results measure retrieval and extraction; they do not measure eligibility decisions. Groundedness was an explicitly labelled token-overlap heuristic on extractive answers. Calibration used the same questions it was tuned on, and the ten missed refusal probes remain a limitation.

**Phase 6 before Phase 5 is a dependency and delivery decision**, recorded on October 13. The engine consumes verified records directly and can work without embeddings, reranking, retrieval, or an LLM. Phase 5 improves evidence retrieval and can be judged against the baseline once the product's core report exists. Completing the engine first also supplies the `check_eligibility` tool needed by the Phase 7 agent. The phase numbers stay unchanged; their execution order changed deliberately.

## 3. Data and rule representation

### Confirmed student profile

Use Pydantic models with a schema version. Represent these families explicitly:

- Citizenship(s), qualifying-degree country, secondary-education country, and current relevant enrolment/residence facts. They are different concepts and must not substitute for one another.
- Degree title/field/institution, completion status, duration, total credits and their unit, and subject/course credit allocations. Coursework supplied by a student is not automatically certified equivalent to a university's modules.
- Original grade and scale; best achievable grade; minimum passing grade; optional officially converted German grade and provenance; class rank where needed. Never assume a national passing mark.
- English/German evidence: test identity, format/scale version, date, overall/component scores, categorical result, and explicitly supported education-based proof. CEFR is a proficiency framework, not a test identity.
- GRE General scores/percentiles separately, GATE paper/year/result, and entrance-exam or university-assessment outcomes. A raw GRE score is not a percentile.
- Document availability, relevant experience, and financial inputs in EUR with an explicit period and proof route.

The check request owns target country, programme slugs, intake/starting year and `as_of`; these must not be overridden by a second copy inside the profile. Target names found in pasted text are unconfirmed suggestions, not permission to map an ambiguous university name to a covered programme.

Missing values are `null`, not fabricated zeros or false booleans. For evidence lists, `null` means not supplied and `[]` means the student explicitly reports none. GRE and GATE are objects, so the literal `"none"` means the student has no such test; `null` and an empty object stay not supplied. Missing credit categories remain unknown unless the student explicitly supplies zero. Reject malformed values; do not reject an otherwise valid incomplete profile. Use Decimal for money, grades, and score comparisons.

### Reviewed rule catalogue

Keep the existing 17-field extraction records and their historical metrics intact. Add a **derived, versioned rule catalogue** in `data/eligibility/`: one programme rule file per existing slug, a cited financial-rule file, and sourced country-group definitions.

Use a small set of typed domain rules: numeric bounds, accepted proof alternatives, credit requirements, applicant conditions, deadlines/document prerequisites, and explicit university-review steps. Support `all_of` and `any_of` groups and conditional applicability; do not build a general scripting language or evaluate arbitrary expressions. Admission alternatives and GRE/GATE alternatives are separate groups.

Every rule records an ID, category, hard/soft/informational status, required milestone, source doc ID(s), supporting quote(s), source snapshot hash, and review provenance. Bind each programme catalogue to a canonical hash of its verified requirement record. A changed record invalidates the derived catalogue until reviewed. Do not silently reinterpret free-text scores, `condition`, degree titles, or selection narratives during a student's request.

Create a 13-programme coverage matrix before coding rules. Classify every stated field as automatically evaluable, informational/readiness, or requiring university/manual review; retain `not_published` separately. Where the current record omits a material condition, consult the cached official source and attach additional validated evidence. Genuine extraction corrections go through Save, preserve tiers, and are recorded as corrections rather than hidden normalization.

Catalogue drafts may be assisted. New semantic interpretations have their own `reviewed_by` status; accepting a catalogue does not promote a programme's verification tier. Unreviewed, stale, conflicting, or unsupported mandatory interpretations cannot produce a positive eligibility headline.

Validate actual quotes against cached sources locally. CI validates schemas, source identities/hashes, record binding, and fixture-based quote checks; it must not claim full live-page verification when raw pages are unavailable.

## 4. Evaluation behavior

### Outcomes and aggregation

Core criterion outcomes remain `meets`, `does_not_meet`, `unknown`, and `not_published`. Add applicability, reason codes, and hard/soft metadata. Show exemptions explicitly and exclude inactive requirements from the requirement count.

- `all_of`: a known failing applicable child fails the group; all passing children pass it; otherwise unknown.
- `any_of`: a passing applicable alternative passes the group; fail only when all applicable alternatives are known to fail; an unresolved possible alternative keeps the group unknown.
- Unknown applicability stays unknown. An unprovided fact must not become an exemption. Reject empty or contradictory rule groups during validation.
- Count top-level requirement groups once. Alternative branches and component scores appear in the trace without inflating the denominator.
- An unmet applicable hard admission rule produces `does_not_meet_published_requirements`. Otherwise unresolved hard facts or university judgment produce `needs_information_or_review`. Only fully resolved applicable hard checks permit `meets_checked_published_requirements`; this does not mean admitted. An uncovered programme produces `not_covered`.
- A soft recommendation cannot reverse the headline. Missing publication is never invented as a requirement or counted as passed. Surface it separately.
- A routine statement that an admission board selects applicants is informational. Only an unresolved published prerequisite or required assessment blocks a checked-requirements headline; do not turn every report unknown merely because a board exists. Use counts and margins, with no weighted eligibility score.
- Report application deadlines/documents and finances in separate summaries; insufficient funds or a missed application window must not be described as an academic qualification failure.

Each criterion returns entered value, required value/operator/unit, verdict, applicability, reason, margin where comparable, action, and citations. A positive margin is favourable: observed minus minimum for minimum-score rules; maximum minus observed for upper bounds such as German grades. Strict inequalities retain their strictness at a zero margin. Actions come from deterministic templates, not an LLM verdict.

### Required corpus-specific behavior

| Rule family | Behavior to implement and test |
|---|---|
| Degree / subject credits | Compare published totals and student-confirmed allocations; no automatic non-ECTS conversion, semantic course classification, or assumption that similarly named degrees are equivalent. University equivalence stays a review step unless the exact published reference qualification or an explicitly reported university assessment resolves it. |
| KIT CS | Separate the subject-credit route, qualifying GATE route, and interview route. Failing one route cannot reject an applicant who satisfies another; an interview invitation is not a passed interview. |
| KIT CDS | Represent the 20-credit basic-maths rule plus 40 in one domain and 12 in each remaining domain, with explicit overlap/counting policy from the source. Represent up-to-12-credit conditional admission separately from unconditional eligibility; pending university approval stays review. |
| RWTH | Distinguish CS degree-country rules from DS citizenship/German-school exemptions. Version EU/EEA/EHEA and any Lisbon-signatory sets from official evidence. Unknown membership cannot be treated as exempt. Preserve strict GRE percentile boundaries. |
| Darmstadt | The exam is conditional on unresolved competencies; GRE/GATE can exempt it. Academic equivalence and formal exam outcomes are separate facts. Apply the same source-faithful interpretation to CS and AIML without inheriting the old flat `one_of` error. |
| English / German | Evaluate accepted proof alternatives and required components; use the supplied TOEFL format/scale, not an assumed conversion across versions. Apply validity dates, allowed home editions, MOI/native-speaker/education conditions, and programme-specific German milestones only when sourced. A generic C1 claim does not prove an accepted certificate. |
| Saarland | Preserve the grade/rank conjunction and the actual alternative grade scales. Respect degree-region GRE/GATE exemptions and the specific English-proof exceptions. Do not infer an unstated numeric GRE/GATE minimum. |
| GATE / GRE | Preserve allowed paper, score type, year, validity, and submission conditions. Evaluate annual qualification from an explicitly reported result/scorecard information; do not invent a year's qualifying cutoff. |
| APS / documents | APS follows the source's degree-country rule. Treat optional documents as optional, preserve conditional VPD/GRE/English evidence, and show pending documents as readiness gaps rather than silently supplied facts. |
| Deadlines | Choose by intake, degree origin, citizenship/applicant class, route, and relevant exceptions. Encode application versus aptitude-registration windows and early/recommended versus final dates separately. Give each recurring date an explicit year offset; summer deadlines may fall in the previous year. Respect published validity periods and inclusive closing dates. |
| Fees / selection | Show fees with period and scope; do not promise a waiver or infer fee liability from citizenship alone. Published admission-board judgment, interviews, rankings, and incomplete selection formulas remain explicit review steps. |

The initial 13-programme matrix must cite which source supports each exceptional branch. Any unresolved interpretation remains visible as unknown; a high automatic-coverage percentage is not a reason to guess.

### Grade conversion and funds

Expose `convert_grade(best, passing, obtained)` using `1 + 3 × (best − obtained) / (best − passing)`. Validate nonzero denominator and the stated passing range, preserve calculation precision, and support scales running in either direction. Letter/nonlinear systems need an explicitly documented numerical mapping; do not invent one. Return inputs, method, full calculation, and a labelled estimate. Prefer an official VPD/university conversion for an official-grade requirement. An estimate alone must not certify official equivalence or decide an uncertain boundary. [TUM describes its calculator as non-binding](https://www.tum.de/en/studies/application/application-info-portal/grade-conversion-formula-for-grades-earned-outside-germany); use its [official formula document](https://www.international.tum.de/fileadmin/w00bwe/www/Wege_ins_Ausland/Studierende/TUMexchange/EN-Bayerische_formel.pdf) as implementation evidence.

The financial check compares entered EUR funds with a reviewed, cited, purpose- and period-specific reference and returns a surplus/shortfall. Keep tuition, semester contribution, living-cost estimates, and visa financial proof separate. Money available is not itself proof that an authority accepts that funding route. Alternative proofs and uncertain exemptions require review. The [Federal Foreign Office states that the required amount depends on the purpose of stay and competent mission](https://www.auswaertiges-amt.de/en/visa-service/visabestimmungen-node/sperrkonto-seite); do not hard-code one amount as universally sufficient. No currency-rate service is needed for this phase.

## 5. Interfaces and profile extraction

Keep the core functions independent of FastAPI, retrieval models, and LLM clients:

- `get_requirements(programme_slug)` returns the cited record and rule-readiness/provenance metadata.
- `check_eligibility(profile, programme_rules, as_of)` returns the structured report; the caller supplies the date so tests are repeatable.
- `convert_grade(...)` and `check_funds(...)` are separately testable helpers and future agent tools.

Add stateless endpoints using existing request IDs and error conventions:

| Endpoint | Contract |
|---|---|
| `POST /eligibility/check` | Confirmed profile plus explicit target country, intake/starting year, `as_of`, and a nonempty deduplicated list of target slugs. A YAML limit defaults to 13 targets per request. Return a report per target. Unknown targets return coverage notices, never requirements borrowed from a similar programme. Unsupported countries receive the Germany-only notice. For stale rules, return that target as unavailable with `needs_information_or_review` and reason `rules_stale`, not applicant failure. |
| `POST /profile/parse` | Plain text up to 16,000 characters to a draft profile; no file uploads or URL fetching. |

Scope trim (2026-10-29): `GET /programmes`, `GET /programmes/{slug}/requirements` and `POST /tools/convert-grade` are deferred to Phases 8–9, when the UI or deployment needs them. The Phase 7 agent and the CLI call `get_requirements` and `convert_grade` as Python functions.

Reports carry request ID, schema/rule versions, input/source hashes, verification tier, intake/as-of context, criterion traces, counts, separate admission/readiness/finance summaries, and unresolved-review reasons. Do not echo an entire personal profile unnecessarily. Do not store or log profile text, fields, or model completions.

Coverage handling here protects eligibility-tool requests. It does not by itself fix the ten missed free-chat refusal probes from Phase 4; retrieval, routing and answer-policy improvements remain in their planned phases.

Text extraction uses the existing thin LLM client and structured output. Return a literal supporting span per populated field, conflicts/missing fields, and an explicitly unconfirmed draft. Validate spans and types; allow one schema-repair attempt. An optional model-assessed confidence value is labelled uncalibrated and never affects eligibility. Unsupported/inferred facts stay blank. Treat instructions embedded in pasted text as data. The check endpoint requires a confirmed profile; the future UI must expose the draft for edits rather than silently checking it.

With no API key, manual JSON profiles, the engine, APIs other than parse, and evaluation still work. Parse returns a clear unavailable response; it must not fabricate a CV parser. Provider failures expose a bounded, profile-free error. Live parse checks are opt-in and use synthetic text only; automated tests use a fake client.

Use the current Python/Pydantic/FastAPI stack, direct SDK wrapper, YAML settings and local files. Add `eligibility*` to package discovery. Keep programme numbers/conditions in cited data rather than scattering them through Python branches. API/CLI wrappers call the same core functions.

## 6. Build sequence and human review

Work uses one branch and one PR per piece of work.

| Step | Runnable increment | Human review and evidence |
|---|---|---|
| 0. Lock the rule inventory (done) | Produce the 13-programme/17-field coverage matrix, source references, unresolved interpretations and the five-profile worksheet (kept local until the cases are frozen). Preserve Phase 4 artifacts and hashes. | Done. The R01–R17 interpretations are not a gate for Steps 1–2; each programme's items are reviewed when its catalogue is built in Step 3, defaulting to the conservative `unknown`. |
| 1. Types and validation (done) | Profile, rule, citation and report models; rule loader/version checks; profile round-trip and invalid-input tests. | Walk through one incomplete profile and explain missing versus zero and unknown versus not published. |
| 2. Deterministic primitives (done, including date predicates and the blocked-account funds check) | Numeric/grade/credit/proof/date/country predicates, all/any logic, margins, funds helper and explicit clock input. | Check worked boundary examples by hand before looking at engine output. |
| 3. Programme rules and reports (done; 19 rules still `pending`) | Populate all 13 catalogues from cited evidence; validate local quotes; add conditional cases and deterministic action text. Run `make eligibility` on a sample JSON profile. | Decide that programme's R-items in a short batch as each catalogue is built (TUM Informatics first, KIT CS next). Review provenance stays separate from record tiers. |
| 4. API and paste-to-fill (done) | Add `POST /eligibility/check`, `POST /profile/parse` and the CLI parse workflow. Demonstrate paste → draft → edit/confirm → report using synthetic text. | Confirm that an ambiguous extraction can be corrected and that no key is needed for manual-profile checking. |
| 5. Independent evaluation (harness built; five cases not frozen; no run) | Validate and run the profile dataset, emit the eligibility results and update its separate README section. | Write five realistic anonymised/synthetic profiles and expected criterion/headline outcomes **before** comparing with engine results; resolve disagreements against citations. |
| 6. Close and explain (not started) | Full tests, lint, existing frontend build, local source/rule validation, CI coverage, a short demo and updated project status. | Run the commands, explain a successful comparison, a real gap and an unknown, then review the decision log entries. |

New Make targets: `eligibility ARGS="--profile ... --programme ... --as-of YYYY-MM-DD"`, `parse-profile ARGS="--input ..."`, and `eval-eligibility`; catalogue validation is a flag of the first. They reuse the same models/functions as the API. Profile JSON can be imported/exported locally; browser storage and the public form wait for Phase 9.

Each step ends with a focused check; do not postpone all testing to the end. Clarify genuine source ambiguity when the step exposes it, while completing independent work. The five human-authored cases and new rule acceptance are the planned human review; no automated step may mark a label human.

## 7. Evaluation and acceptance

Create **40 synthetic profile–programme cases**, with stable case IDs, profile facts, target programme, fixed date/intake, expected top-level and selected criterion outcomes, rationale/citations, author, and reviewer. Include five human-authored cases and 35 assisted cases; cover every programme at least twice, using the remaining 14 slots for adversarial/boundary cases. Reused profile variants are identified as related cases, not claimed as independent observations.

Expected results are written from sources, not generated from the engine under test. Report the five human-authored cases separately. Preserve assisted authorship and review labels as honestly as in Phase 4.

Tests and dataset scenarios must include:

- Exact numeric thresholds and strict inequalities; missing versus zero; min-score direction versus German-grade direction; decimal money/score arithmetic; malformed grade scales and unsupported credit units.
- Alternative proof/route pass, fail and unknown combinations; inactive and unresolved conditions; hard versus soft outcomes; no double counting of child checks.
- Nationality versus degree country versus school country; APS; EU/EEA/EHEA and relevant treaty membership; applicant exceptions and stale group definitions.
- Both TOEFL formats, IELTS component failures, expired certificates, permitted/unpermitted MOI and native-education exemptions; missing alternative evidence.
- KIT route/interview and credit-allocation/conditional-admission cases; Darmstadt document assessment versus exam exemption; GRE percentiles and GATE paper/year distinctions.
- Previous-year summer deadlines, early/recommended/final dates, last-day boundaries, route/degree-origin differences, and source period limits.
- Unknown programmes/countries, university-only equivalence, source conflicts, stale rule hashes, unsupported predicates, and source/citation changes.
- Funding shortfalls and unrelated fee periods; prompt-injected/ambiguous profile text; unconfirmed drafts; no-key/provider failure; tests proving the core never calls retrieval or an LLM and does not write real profiles/artifacts.

`make eval-eligibility` writes `evaluation/results/eligibility_baseline.json`: exact headline and criterion agreement, false-positive eligibility count, automatic-check coverage, unknown reasons, per-programme counts, review/author splits, latency, and source/rule/dataset hashes. Report arithmetic/pass checks as comparisons against entered facts; do not call them official admission verification. Keep missing facts, unsupported automation, and university judgment distinguishable in the unknown breakdown.

Acceptance requires all five human cases and all accepted synthetic expectations to match, **zero false-positive eligibility headlines** against those labels, no silently skipped applicable hard requirement, and all 13 programme catalogues accounted for. A justified `unknown` is correct; returning unknown for everything is exposed by the coverage breakdown. Publish actual latency rather than an invented performance claim. Fixture-based core/API tests and rule validation run in CI without model downloads or provider calls; the existing full suite and frontend build remain green.

Add a separate eligibility section/artifact; preserve the Phase 4 retrieval dataset, original audit scores, and benchmark snapshot. If new official rule sources change the retrieval corpus, version that change and run the unchanged retrieval configurations on the final corpus before Phase 5 ablations. Do not attribute a corpus change to a retrieval improvement.

Closure includes a runnable synthetic demo, README examples and measured results, and dated DECISIONS entries on rule normalization, uncertainty/alternatives, conservative conversion, and evaluation provenance.

The demonstration should answer: **Where did this rule come from? Why did this verdict occur? What changes if one fact changes? When does the engine abstain? How was it tested independently? What is its measured cost?**
