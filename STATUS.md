# Status (handoff)

Local only (gitignored). Read this first in every session, then `docs/PROJECT_PLAN.md`.
Update it at the end of every session and at every "Commit Phase N": rewrite **Now** and **Next**, add one line to **Log**.

## Now
- **Phase 4 complete locally** at `b85ae75` (audit and gold review recorded, `make eval` numbers, refusal calibration 4/14 caught, 3/90 falsely refused). PR #4 open, not merged.
- **Phase 6 in progress** on `phase-6-eligibility-engine` (stacked on Phase 4). Step 0 done: coverage matrix (13 programmes x 17 fields), R01-R17 interpretation packet, blank five-profile worksheet, `scripts/validate_phase6_inventory.py` (+ test, Make target, CI step). No engine code yet.
- Scope trimmed 2026-10-29: HTTP surface limited to `POST /eligibility/check` and `POST /profile/parse`; R-review is decided per programme at Step 3, not an upfront gate.
- Tests: 71 pass (full suite without `tests/test_review.py`, which stalls in the sandbox).

- Step 1 done: `eligibility/` (`profile.py`, `rules.py` with closed check set + record-hash binding, `report.py`), `paths.rules_dir`, `tests/test_eligibility_types.py` (8 tests).
- Step 2 done: `eligibility/grade.py` (`convert_grade`), `eligibility/engine.py` (`evaluate`, `check_funds`, `check_eligibility`: bounds with margins, all_of/any_of, headline rules), `tests/test_eligibility_engine.py` (25 tests). Not yet built, on purpose: applicability conditions, country-group and date predicates (Step 3 adds them when a real rule needs them).

- Step 3 started: `when`/`in` checks, `not_applicable`, GRE/GATE fields, language results looked up by test name, `make eligibility` (`--validate` checks staleness and rule quotes). `data/eligibility/rules/tum-m-sc-informatics.json`: degree, GRE/GATE and aptitude `human` (T1, T3, T4 accepted); English written from the cached page and `pending`; APS/VPD readiness `pending`. 48 eligibility tests pass. C1-C10 accepted 2026-10-29 (recorded in LEARNING).
- KIT CS rules written (`data/eligibility/rules/kit-m-sc-computer-science.json`, all `pending`): degree + ECTS, selection entry (GATE | full credits | interview route with 3-of-4 areas, top 10%, interview outcome), GRE/GATE condition, test age, English. Open until built: country groups (R06) and date rules, so KIT can't be positive yet. `interview_passed` added to the profile.
- Country groups built (EHEA 49, Lisbon 57, EU 27; sources and 2026-10-29 fetch date in `data/eligibility/country_groups.json`, re-check after 2027-10-29): `@GROUP` values in rules, three-way membership (member / uncertain / not a member), report notices for old lists. KIT CS GRE rule now depends on the degree country and is `human`. Test-age rules still deliberately not built. 76 eligibility tests pass.
- Finding: parser drops the English accordion on the TUM language page (`<main>` closed early), so chunks and the extraction lack TUM's English thresholds. Deferred to Phase 5 together with the TUM `english` correction (Save checks quotes against the cleaned text, so the correction needs the parser fix first). TUM English rule accepted `human`.

- Step 3 batch: prep committed `5685fd9` (numeric `in` matches, `grade.percent_of_best`, `german_level`, `docs/PHASE_6_RULE_AUTHORING.md`). Rule files for the other 11 programmes + 5 test files written, all `pending`, **uncommitted** (16 untracked paths). `--validate` 13 files OK, 174 eligibility tests pass, ruff clean, Phase 4 hashes unchanged. One combined decision list: `docs/PHASE_6_RULE_DECISIONS.md` (X1-X4 cross-cutting, D01-D26, skim table, gaps).

## Next
1. **Maintainer:** answer `docs/PHASE_6_RULE_DECISIONS.md` in one message ("accept all except ...").
2. **Claude (Step D):** apply answers (X2/X3/D05 change files if accepted), set accepted rules `human`, add the 5 test files to CI, LEARNING Step 3 batch section, PROJECT_PLAN Phase 6 row, commits per university group + docs.
3. **Maintainer:** write the five profiles in `docs/PHASE_6_FIVE_PROFILE_WORKSHEET.md` before Step 5.

## Log (newest first)
- 2026-10-29: Phase 6 Step 3 batch: prep committed; 11 rule files written by five parallel workers from the authoring guide, merged and spot-checked (RWTH CS, Saarland CS); combined decision list ready, awaiting the maintainer.
- 2026-10-29: Phase 6 Steps 1-2 built and Step 3 started (TUM Informatics rules) and committed. Reviewed Step 0 against the plan. Fixed stale STATUS/CLAUDE.md, trimmed Phase 6 endpoints and the review gate, ignored `graphify-out/`.
- 2026-10-27: Phase 6 Step 0 inventory drafted on `phase-6-eligibility-engine`; nothing committed.
- 2026-10-26: Phase 4 committed (`b85ae75`); PR #3 merged; PR #4 opened, not merged.
- 2026-10-23: Committed Phase 3 (data + docs, no attribution), pushed, opened PR #3. Verified the 7 remaining programmes by a second pass over their cited pages; 13/13 saved via the review Save path.
- 2026-10-20: Audited Phase 3 state on disk; pushed 7 unpushed commits.
- 2026-10-16: Extract run (6 of 13; 7 failed on Google 503); cross-checked the 6; approved and added 19 sources (72 sources, 13 programmes).
- 2026-10-13: Phase 3 step 4 (review screen, model fallback list, test-name aliases). Phase 6 moved before Phase 5.
- 2026-10-08: Phase 3 step 3 (extractor built and run on the 8 pilots).
- 2026-10-07: Started Phase 3; fixed 16 oversized chunks; created `LEARNING.md`.
- 2026-10-06: Scope finalised (Germany only). Ran crawl/ingest/index; explained Phase 2.
- 2026-10-05: Phase 2 build; Phase 1 merged (PR #1); plan committed.
- 2026-10-04: Repo repurposed from EngineerDoc AI to the study-abroad assistant.
