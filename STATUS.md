# Status (handoff)

Local only (gitignored). Read this first in every session, then `docs/PROJECT_PLAN.md`.
Update it at the end of every session and at every "Commit Phase N": rewrite **Now** and **Next**, add one line to **Log**.

## Now
- Phases 1-4 merged. Phase 4 baseline (PR #1), the Phase 6 engine plus rule files (PR #2) and the Step 3 rule decisions (PR #3, `e36c977`) are on `main`. Nothing is unpushed or uncommitted.
- Step 3 done: 13 rule files; 70 rules in the 11 new files are `human`; KIT CS selection/English/`degree`/`test_validity` and TUM `aps`/`vpd` stay `pending`.
- Step 4 (API + paste-to-fill) NOT started on purpose: the profile and report shapes are not final (see Next 2).
- Five-profile worksheet (H01-H05): DRAFT, not frozen. `docs/working/PHASE_6_FIVE_PROFILE_SOURCE_CHECK.md` holds excerpts read 2026-11-04 for S1-S15; the maintainer is checking them. Rows needing a maintainer reading: S7 funds (loan/scholarship bullets read as additions, not alternatives), S3 form exemption wording, S6 length/ECTS, S14 formula clause.
- Engine facts confirmed from code: `Report` has one headline (no admission/readiness/finance summaries); no date logic or deadlines; no financial rule file; the engine never emits `not_published`; `gre: None` and an empty `Gre()` both resolve to "unknown", so "no GRE" cannot be entered.

## Open decisions (maintainer)
1. **Degree-equivalence policy.** A: soften TU Berlin `degree`/`subject_allocation` and KIT CDS `degree`/`credit_counting` to informational (H01/H04 can be positive). B: keep them hard; a positive headline needs the student to report the university's assessment (extend X1 to cover degree AND subject allocation). Recommendation: B, because plan section 6 says equivalence "stays a review step unless ... an explicitly reported university assessment resolves it" and section 4 blocks on "required assessment". Under B, H01/H02/H04 headlines become `needs_information_or_review` before the freeze.
2. **`not_published` rows.** Recommended: explicit info rules ("no minimum published") per programme, no effect on the headline. Or drop those rows from the labels.
3. **Credit unit.** Recommended: closed choice "ECTS" / "other". Alternative: accept "LP", "CP", "ECTS credits" as ECTS.

## Next
1. **Build session, no decisions needed (each on its own descriptively named branch, tests first, PR not merged):** (1) Report summaries: admission / readiness / finance, counts, versions/hashes; (2) explicit "no GRE/GATE" answer; (5) evaluation harness (`make eval-eligibility`, dataset schema, validator, metrics; never run on H01-H05 before the freeze).
2. **Then:** (3) date logic + deadline readiness; (4) finance rule file + funds with proof routes (lone blocked account compared; any other route "unknown"); then X1 per decision 1; then Step 4.
3. **Maintainer:** finish the source check, answer decisions 1-3, freeze H01-H05 by committing the labels as `author: human` in a dataset file BEFORE any evaluation code runs on them (commit date is the proof). Then the 35 assisted cases.
4. Local `--check-cache` run (`make eligibility ARGS="--validate --check-cache"`) before relying on quotes taken from cached pages.
5. Stale doc to refresh: `docs/PHASE_6_IMPLEMENTATION_PLAN.md` header and section 6 (still mention PR #4).

## Cloud notes
- New container: `make install` (venv) first; `data/raw` is absent, so cached-page quote checks are skipped. Page reading works through the Firecrawl connector only; direct downloads and the fetch agents are blocked by the network allowlist.
- Git: commits authored as the repo owner (`-c user.name`/`user.email`), no attribution trailers, descriptive branch names, stage files explicitly, `make check-publish` before each commit, repo is private.

## Log (newest first)
- 2026-11-04: Source-check sheet written (S1-S15); vague session branch deleted locally (no unique commits; remote ref already gone); next-build list and open decisions recorded.
- 2026-11-04: Reviewed the pasted worksheet against the plan and merged rules (no engine run); not frozen.
- 2026-11-02: Step 3 decisions applied (accept all except D14, corrected); 70 rules `human`; PR #3 merged by the maintainer.
- 2026-10-29: Phase 6 Step 3 batch written; Steps 1-2 built; TUM Informatics rules.
- 2026-10-27: Phase 6 Step 0 inventory drafted.
- 2026-10-26: Phase 4 committed (`b85ae75`); merged later as PR #1 and #2.
- 2026-10-13 and earlier: Phases 1-3 built; Phase 6 moved before Phase 5; scope Germany only.
