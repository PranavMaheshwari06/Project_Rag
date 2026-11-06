# Maintainer actions

Private working paper (gitignored; lives only on branch `handoff-private`). Numbered; each item says where to do it, the exact commands, what it blocks, and how to answer in one line. Answer by editing the "Answer:" line and pushing to `handoff-private`, or in the next session's first message.

Legend: **BLOCKING** = a later build step waits for it. **NOT BLOCKING** = work continues without it.

> Updated 2026-11-06: ACTIONS 1, 2, 3, 4, 5, 7, 12a, 12k and 12m are done (F1-F4 accepted, all merged as PRs #15-#25; `--check-cache` passes). PR numbers below are the old closed ones. Still open: 6, 8, 9, 10, 11, 12b-12j, 12l. Script and doc names changed: see `CLAUDE.md`.

## 1. Sync your computer without overwriting your worksheet — BLOCKING (for everything else on your computer)
Where: your computer, VS Code terminal in the repo.
```bash
git fetch origin
git show origin/handoff-private:STATUS.md > STATUS.md
git show origin/handoff-private:docs/working/MAINTAINER_ACTIONS.md > docs/working/MAINTAINER_ACTIONS.md
git show origin/handoff-private:docs/working/PHASE_6_FIVE_PROFILE_SOURCE_CHECK.md > docs/working/PHASE_6_FIVE_PROFILE_SOURCE_CHECK.md
```
Do NOT run the same for `docs/working/PHASE_6_FIVE_PROFILE_WORKSHEET.md`: the copy on `handoff-private` is the old blank one; your local copy holds your H01-H05 draft.
Blocks: reading the current state locally.
Answer: "synced".

## 2. Run the cached-page quote check where data/raw exists — BLOCKING (before relying on any quote taken from a cached page)
Where: your computer.
```bash
make install
make eligibility ARGS="--validate --check-cache"
```
`--check-cache` makes a quote that is not in the verified record and whose cached page is missing an error instead of a "not checked" line. Paste the last lines of the output into the answer.
Blocks: trusting the TUM English, KIT CDS English and D05 quotes, and every new quote added in this session (listed under item 12).
Answer: "N rule files OK" or the error lines.

## 3. Degree-equivalence policy A or B — BLOCKING (X1 build, label freeze of H01/H02/H04)
Where: decide anywhere; answer in this file.
- A: soften TU Berlin `degree` / `subject_allocation` and KIT CDS `degree` / `credit_counting` to informational, so H01/H04 can be positive.
- B (recommended): keep them hard; a positive headline needs a reported university assessment (one profile fact "university assessment on file" resolves both the degree rule and the allocation/credit-counting rule). Plan section 6 keeps equivalence "a review step unless ... an explicitly reported university assessment resolves it". Under B you re-label H01/H02/H04 yourself before the freeze.
Blocks: stage F3 acceptance; freezing H01/H02/H04.
Answer: "A" or "B".

## 4. `not_published` rows: explicit info rules or drop — BLOCKING (stage F2 acceptance, label freeze)
Where: answer here.
- Recommended: explicit info rules ("no minimum published") per programme, no effect on any headline.
- Or: drop those rows from the labels.
Answer: "info rules" or "drop".

## 5. Credit unit: closed choice or aliases — BLOCKING (stage F1 acceptance)
Where: answer here.
- Recommended: closed choice "ECTS" / "other"; "other" stays "the university decides".
- Or: accept aliases ("LP", "CP", "ECTS credits") as ECTS.
Answer: "closed" or "aliases".

## 6. Finish the source sheet, then freeze H01-H05 — BLOCKING (Step 5 evaluation on the five cases)
Where: your computer (VS Code), `docs/working/PHASE_6_FIVE_PROFILE_SOURCE_CHECK.md` and your local worksheet.
- Rows still needing your reading: S7 funds (loan/scholarship bullets read as additions, not alternatives; see 12i), S3 Suitability Assessment Form exemption wording, S6 first-degree length/ECTS (section 3 of the PDF), S14 conversion formula clause.
- Then commit H01-H05 as `author: human` with `frozen_on` in `evaluation/datasets/eligibility_cases.jsonl` (one JSON object per line; schema `evaluation/eligibility_dataset.py`, PR #8) BEFORE any evaluation code runs on them. The commit date is the proof of the freeze. Each line needs: `case_id`, `profile` (profile-v3, or v4/v5 if you accept F1/F3; a funds case needs `funds` and `visa_country`), `slug`, `intake` (winter/summer), `starting_year`, `as_of`, `expected_headline`, `expected_criteria` (each with `rule_id`, `verdict`, at least one citation), `rationale`, `citations`, `author: "human"`, `reviewer`, `related_to` (or null), `frozen_on`. The validator refuses `author: human` without `frozen_on` and a `frozen_on` in the future.
- There is no validate-only mode: `make eval-eligibility` runs the engine as soon as validation passes. So: commit and push the labels first, then run it.
Blocks: any engine run on the five cases.
Answer: "frozen at <commit>".

## 7. Review and merge the PRs in order — BLOCKING (each later branch)
Where: GitHub, repo PranavMaheshwari06/Project_Rag, Pull requests tab.
Merge order and bases are in the branch table in `STATUS.md`. Retarget a stacked PR to `main` after its base merges (GitHub offers this automatically when the base branch is merged and deleted; otherwise edit the PR base).
Answer: "merged #N, #M".

## 8. Deadlines for the other programmes — NOT BLOCKING
Where: official pages; add each as a row in the source-check sheet.
Deadline readiness rules exist only for KIT CDS (S10) and KIT CS (S11) (PR #9, pending). Still to source (data, no code): TU Berlin CS (S1 was read, but its dates page https://www.tu.berlin/en/go167 is not in `sources/registry.yaml`; adding it changes the corpus and needs `make crawl` — decide whether to add it), RWTH CS, RWTH DS, Saarland CS, Saarland DSAI, TU Darmstadt CS, TU Darmstadt AIML, TU Dresden CS, TUM Informatics, TUM DEA, Stuttgart CS.
Answer: "sourced: <slugs>".

## 9. The 35 assisted-case slots — BLOCKING (assisted part of Step 5)
Where: answer here; labels are written later from sources, not from engine output.
Approve, change or drop each slot (programme x scenario). No labels are written yet.

Coverage slots (each programme twice):
| # | Programme slug | Scenario |
|---|---|---|
| A01 | tum-m-sc-informatics | all checked hard requirements met at a numeric boundary |
| A02 | tum-m-sc-informatics | one fact missing (unknown, not a failure) |
| A03 | tum-m-sc-data-engineering-and-analytics | boundary met |
| A04 | tum-m-sc-data-engineering-and-analytics | one known shortfall |
| A05 | rwth-aachen-m-sc-computer-science | boundary met |
| A06 | rwth-aachen-m-sc-computer-science | one known shortfall |
| A07 | rwth-aachen-m-sc-data-science | boundary met |
| A08 | rwth-aachen-m-sc-data-science | one fact missing |
| A09 | tu-berlin-m-sc-computer-science | boundary met |
| A10 | tu-berlin-m-sc-computer-science | one known shortfall |
| A11 | saarland-university-m-sc-computer-science | boundary met |
| A12 | saarland-university-m-sc-computer-science | one fact missing |
| A13 | saarland-university-m-sc-data-science-and-artificial-intelligence | boundary met |
| A14 | saarland-university-m-sc-data-science-and-artificial-intelligence | one known shortfall |
| A15 | tu-dresden-m-sc-computer-science | boundary met |
| A16 | tu-dresden-m-sc-computer-science | one fact missing |
| A17 | kit-m-sc-computer-science | boundary met |
| A18 | kit-m-sc-computer-science | one known shortfall |
| A19 | kit-m-sc-computational-and-data-science | boundary met |
| A20 | kit-m-sc-computational-and-data-science | one fact missing |
| A21 | tu-darmstadt-m-sc-computer-science | boundary met |
| A22 | tu-darmstadt-m-sc-computer-science | one known shortfall |
| A23 | tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning | boundary met |
| A24 | tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning | one fact missing |
| A25 | university-of-stuttgart-m-sc-computer-science | boundary met |
| A26 | university-of-stuttgart-m-sc-computer-science | one known shortfall |

Adversarial / boundary slots:
| # | Programme slug | Scenario |
|---|---|---|
| A27 | rwth-aachen-m-sc-computer-science | GRE percentile exactly at a strict bound |
| A28 | rwth-aachen-m-sc-data-science | EU citizen with an Indian degree (citizenship vs degree country) |
| A29 | kit-m-sc-computer-science | GATE route passes while subject credits fail |
| A30 | kit-m-sc-computational-and-data-science | up to 12 credits missing (conditional admission is the university's call) |
| A31 | tu-darmstadt-m-sc-computer-science | GRE/GATE exempts the exam; document assessment still open |
| A32 | saarland-university-m-sc-computer-science | grade met, class rank missing (conjunction) |
| A33 | tum-m-sc-informatics | TOEFL new 1-6 scale vs old 0-120 scale |
| A34 | tu-berlin-m-sc-computer-science | application on the last day vs the day after the window |
| A35 | university-of-stuttgart-m-sc-computer-science | credits in a unit other than ECTS |

Answer: "approve all" or the slot numbers to change.

## 10. DECISIONS drafts to rewrite — NOT BLOCKING
Where: `DECISIONS.md` on the PR branches (DRAFT entries dated 2026-11-02). Rewrite in your own words when convenient.
Answer: "rewritten".

## 11. Optional live parse check with your own key — NOT BLOCKING (only after stage F4 exists)
Where: your computer, `.env` with your key (never commit it). Use synthetic text only.
```bash
make parse-profile ARGS="--input <synthetic text file>"
```
Answer: "parse ok" or the error.

## 12. Session items (added as the stages run)

### 12a. Remove the tool footer from PR bodies — BLOCKING (before any merge: a squash merge can copy the body into history)
Where: GitHub, PRs #4-#14, "Edit" on the PR description.
The cloud PR tool appends a "Generated by ..." footer on every create or edit and re-appends it after removal, so it could not be removed from the session. Delete the last `---` line and the footer line by hand.
Answer: "footers removed".

### 12b. Stage A report summaries (PR #5) — accept or change the area headline words — NOT BLOCKING
Readiness: `ready_on_checked_items` / `items_still_needed` / `needs_information_or_review` / `no_checked_items`. Finance: `funds_cover_checked_reference` / `funds_shortfall` / `needs_information_or_review` / `no_checked_items`. Only hard rules set an area headline (as for admission), so an area with only soft rules reads `no_checked_items`.
Answer: "accept" or the words to change.

### 12c. RWTH CS English and German rules are tagged `readiness` — NOT BLOCKING
Found by the Stage A spec review (agent review, not verified by a person): in `data/eligibility/rules/rwth-aachen-m-sc-computer-science.json` the English and German proof rules have `category: readiness`, so a failed language proof reads as `items_still_needed`, not as an admission failure. This was in the accepted 2026-11-02 rule file; nothing was changed. Decide whether that is intended (e.g. proof due by enrolment) or should be `admission`.
Answer: "intended" or "make admission".

### 12d. Stage B (PR #7): accept the literal "none" for GRE/GATE — NOT BLOCKING
`gre: "none"` / `gate: "none"` = the student has no such test; `null` or `{}` = not supplied. Profile schema `profile-v2`. Alternative was a boolean flag per test. If accepted, a DECISIONS entry is owed.
Answer: "accept" or "use a flag".

### 12e. Stage C (PR #8): eval harness choices — NOT BLOCKING
Author values are `human` / `assisted`; reviewer `human` / `model` / null; `not_covered` is refused in cases (only the Step 4 API can produce it); coverage counts every applicable hard and soft criterion (all three areas).
Answer: "accept" or what to change.

### 12f. settings.yaml is hash-locked as a Phase 4 input — NOT BLOCKING
`data/eligibility/coverage_inventory.json` locks `config/settings.yaml`, so Phase 6 settings (rules dir, country groups, eval paths) are Python defaults in `core/config.py`. To move them into YAML, the lock must be refreshed deliberately (`scripts/validate_phase6_inventory.py` never refreshes it implicitly). Same for `evaluation/datasets/README.md` (locked), which therefore has no section on the eligibility dataset yet.
Answer: "keep code defaults" or "refresh the lock and move them".

### 12g. Stage D (PR #9): review the four KIT deadline rules — BLOCKING (a positive readiness headline for KIT)
Rules `deadline_winter` / `deadline_summer` in `kit-m-sc-computer-science.json` and `kit-m-sc-computational-and-data-science.json`, all `pending`. KIT CDS: 30 Sep / 31 Mar for German and EU nationals, 15 Jul / 15 Jan for non-EU nationals (page read 2026-11-04). KIT CS: 15 Jun / 15 Jan for everyone. Its verified record says `deadlines: not_published` for KIT CDS: an extraction omission; decide whether to correct the record through the Save path.
New quotes to check with ACTION 2: KIT CDS "German and EU nationals First semester: September 30 for winter term, March 31 for summer term", "Non-EU nationals First semester: July 15 for winter term, January 15 for summer term" (de/kit/cds-msc/programme); KIT CS "First semester: June 15 for winter term, January 15 for summer term" (de/kit/cs-msc/programme).
Open questions: EEA/Swiss citizens get the non-EU dates (the page says "EU nationals"); `citizenships: []` reads as non-EU (as in the RWTH DS rule).
Answer: "accept" or the rule ids to change.

### 12h. KIT CS test age (`test_validity`) — NOT BLOCKING
`max_age` now exists, but encoding "GRE not older than 5 years, GATE 3 years" correctly means folding it into the accepted `gre_or_gate` rule (a passing but stale GRE must not count). That changes an accepted rule, so it is your call; the reference date is also unstated on S12 (the engine would use the request's `as_of`).
Answer: "fold into gre_or_gate (back to pending)" or "keep as review".

### 12i. Stage E (PR #10): review the visa funds rule — BLOCKING (any positive finance headline)
Rule `blocked_account_first_year` in `data/eligibility/finance.json` (pending): `visa_country` India; a lone blocked account >= 11,904 EUR; any other route or combination "unknown". Quotes to check with ACTION 2: the S7 blocked-account bullet (de/rules/embassy-india-studies-visa) and the S8 sentence "The blocked account must have sufficient credit ... (unless other proof of financial support is presented in addition)." (de/rules/foreign-office-blocked-account). The cached copies are from 2026-10-05; `fetched_on` is the 2026-11-04 live read.
Choices to confirm: profile-v3 route list (S7 + S9 names); combinations stay unknown even when the blocked account alone covers the amount (literal reading of the spec); the 992 EUR monthly limit is stated, not checked; no period field (the S7 amount is for the first year by definition); the old `funds_eur` total and `check_funds` helper stay (keep, or remove in a later schema version); a scope by citizenship was dropped because S7 does not state one. A DECISIONS entry is owed once accepted.
Answer: "accept" or what to change.

### 12j. Country spelling — NOT BLOCKING
(Done: `--check-cache` now covers the finance quotes; #4 is merged into #9, so merge #4 first.) `visa_country` and citizenship values are matched case-insensitively but not trimmed (" India" does not match), as before for all country facts.
Answer: "do it" or "skip".

### 12k. Provisional branches F1-F4 — accept or revert each — BLOCKING (each is unmerged until you decide)
All are provisional: every commit message says so. Merge only the ones you accept (after #10); close the PR of the others.
- F1 `provisional-credit-unit-closed-choice` (PR #12; answers ACTION 5 with "closed"): profile-v4, `credit_unit` is "ECTS" or "other"; free text is refused. Tests that used "US credits"/"CP" now use "other" with the same expected verdicts.
- F2 `provisional-not-published-info-rules` (PR #11, answers ACTION 4 with "info rules"): check type `not_published` (info only, never counted); rules for TU Berlin IELTS section scores, KIT CS minimum grade, KIT CDS GRE/GATE, taken from the source-check sheet because your filled worksheet was not available here; add or remove rows as your worksheet says.
- F3 `provisional-university-assessment-fact` (PR #13; answers ACTION 3 with "B"; stacked on F1): profile-v5 `university_assessments` {programme slug: positive|negative}. Changed accepted rules, now back to `pending`: TU Berlin `degree`, `subject_allocation`; KIT CDS `degree`, `credit_counting`. The other 11 programmes' degree rules are unchanged (still "the university decides"); extend if you want X1 everywhere.
- F4 `provisional-eligibility-api-profile-parse` (PR #14): POST /eligibility/check (no key needed, max 13 targets, deduplicated, not_covered / rules_stale / Germany-only notices), POST /profile/parse (16,000 characters, literal spans, one repair, 503 without key, 502 on provider errors, nothing logged), `make parse-profile`. The 13 and 16,000 limits are code defaults, not YAML, because settings.yaml is hash-locked (ACTION 12f).
Merge conflicts to expect: F2 vs F3 on the pending-rule sets in two test files (take the union).
Answer: "accept F1 F2 F3 F4" or the ones to revert.

### 12l. CI turns red on 2027-05-05 unless the funds amount is re-read — NOT BLOCKING until then
`make eligibility ARGS="--validate"` (and so CI) fails once today is past `recheck_after` in `data/eligibility/finance.json` (2027-05-04), as it does for the country lists (2027-10-29). Re-read S7/S8, update the amount, `fetched_on` and `recheck_after`.
Answer: "re-read on <date>".

### 12m. Docs to update after you decide the provisional branches (from the final audit) — NOT BLOCKING
- F1 accepted: LEARNING "The credit unit is free text"; PHASE_6_RULE_AUTHORING `credit_unit` type -> "ECTS" | "other"; profile version v4. Also known and unchanged: Saarland's credit rules have no "not ECTS" branch (so "other" fails there), and subject-area credits are compared as ECTS whatever the unit.
- F2 accepted: PHASE_6_RULE_AUTHORING check table gets `not_published`; the pending-rule lists in PLANNING_INDEX, PHASE_6_IMPLEMENTATION_PLAN step 3 and PROJECT_PLAN Phase 6 row get the 3 new rules.
- F3 accepted: DECISIONS (append an "Updated" line, never edit) and LEARNING X1 "not built" -> built for TU Berlin and KIT CDS; pending lists get TU Berlin degree/subject_allocation and KIT CDS degree/credit_counting; profile facts table gets `university_assessments`; profile v5.
- F4 accepted: README status/roadmap ("API comes next"), README "No API key is needed" -> except /profile/parse; README command block gets `make parse-profile`; PHASE_6_IMPLEMENTATION_PLAN Step 4 status; PROJECT_PLAN "Remaining: ... the API"; CLAUDE.md API router list.
- DECISIONS entries owed after acceptance: no-GRE literal (B), harness choices (C), deadlines (D), funds rule (E), and each accepted F branch.
Answer: "done".

