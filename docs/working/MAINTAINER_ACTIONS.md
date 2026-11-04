# Maintainer actions

Private working paper (gitignored; lives only on branch `handoff-private`). Numbered; each item says where to do it, the exact commands, what it blocks, and how to answer in one line. Answer by editing the "Answer:" line and pushing to `handoff-private`, or in the next session's first message.

Legend: **BLOCKING** = a later build step waits for it. **NOT BLOCKING** = work continues without it.

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
- Rows still needing your reading: S7 funds (loan/scholarship bullets read as additions, not alternatives), S3 Suitability Assessment Form exemption wording, S6 first-degree length/ECTS (section 3 of the PDF), S14 conversion formula clause.
- Then commit H01-H05 as `author: human` with `frozen_on` in `evaluation/datasets/eligibility_cases.jsonl` (one JSON object per line; schema `evaluation/eligibility_dataset.py`, PR #8) BEFORE any evaluation code runs on them. The commit date is the proof of the freeze. Each line needs: `case_id`, `profile` (profile-v2), `slug`, `intake` (winter/summer), `starting_year`, `as_of`, `expected_headline`, `expected_criteria` (each with `rule_id`, `verdict`, at least one citation), `rationale`, `citations`, `author: "human"`, `reviewer`, `related_to` (or null), `frozen_on`. The validator refuses `author: human` without `frozen_on` and a `frozen_on` in the future.
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

### 12a. Remove the tool footer from PR bodies — NOT BLOCKING
Where: GitHub, each PR opened in this session (#4 onwards), "Edit" on the PR description.
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

