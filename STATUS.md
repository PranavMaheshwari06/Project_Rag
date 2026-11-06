# Status (handoff)

Local only (excluded from git; the copy of record is on branch `handoff-private`). Read this first in every session, then `docs/project-plan.md`.
Update it at the end of every session: rewrite **Now** and **Next**, add one line to **Log**.

In progress: none.

## Now
- `main` = `f8d9fec`, CI green. Branches: `main` and `handoff-private` only. Installs use uv and `requirements.lock`.
- Checks on `main` (2026-11-06): full suite 456 passed, ruff clean, inventory with `--check-cache` OK, `--validate --check-cache` 13 rule files OK. Hybrid+rerank MRR 0.774, Recall@5 0.872, p50 about 2.5 s.
- Merged and accepted: report summaries, no GRE/GATE, eval harness, deadlines and test age, visa funds, credit unit, university assessment (TU Berlin and KIT CDS), no-minimum rules, API and paste-to-fill.
- 19 rules are `pending`: KIT CDS degree, credit_counting, gre_gate, both deadlines; KIT CS degree, degree_ects, module_assignment, test_validity, english, min_grade, both deadlines; TU Berlin degree, subject_allocation, english_components; TUM aps, vpd; funds blocked_account_first_year.

## Next (maintainer)
1. Review the 19 pending rules (ACTIONS 12g, 12i and the F3 rules).
2. Compare F2's no-minimum rules with the worksheet: it marks more rows not_published (e.g. TU Berlin grade and GRE/GATE, KIT CDS grade). Worksheet cases in LP must use `ECTS` or `other`.
3. Finish the source check and freeze H01-H05 in `evaluation/datasets/eligibility_cases.jsonl` BEFORE `make eval-eligibility` runs on them.
4. Approve the 35 case slots (ACTION 9). Rewrite DRAFT entries and the new 2026-11-06 entry in `DECISIONS.md`; line 171 still names LEARNING.md.
5. Add bootstrap confidence intervals to the eval (from `some_to_do.txt`; size and latency are already reported).
6. Before deploy: `/profile/parse` privacy notice and provider decision. CI fails on purpose after 2027-05-04 (funds re-read) and 2027-10-29 (country lists).

## At public launch
Publish filtered history to a new public repo (GitHub keeps PR description edit history here, so old footers stay visible on closed PRs), delete `handoff-private`, choose a licence, rename the repo, turn on branch protection.

## New clone or cloud session
`make install` (needs uv); copy `docs/working/pre-commit.hook` to `.git/hooks/pre-commit` and add the tool ignores to `.git/info/exclude`. Commits authored as the repo owner, no attribution trailers, stage files explicitly.

## Log (newest first)
- 2026-11-06: Cleanup: 11 engine PRs merged as #15-#25 (old #4-#14 closed by a branch rename, replaced by one-commit PRs); F1-F4 accepted from the spec after a combined local run (456 tests, cached quotes, identical benchmark); branches cleaned, squash-only; files renamed (#27); benchmark and lock refreshed (#28); moved to uv with requirements.lock (#29), indexes and scores identical.
- 2026-11-04: Final audit (agent, whole repo): #4 conflicted with #9/#10 on the CLI usage lines, so #4 was merged into #9 and forward (now merge #4 first); `--check-cache` now covers the finance quotes (#10); docs reworded for the merged state; PR-number references fixed. Full suite on #14: 434 passed. CI green on every PR head checked.
- 2026-11-04: F1-F4 reviewed (combined agent reviews) and fixed; PRs #11-#14 opened. CLI/API tests now patch `get_settings` because the full-suite corpus fixture (tests/conftest.py) repoints the shared cached settings; fix committed on #9 and #10 and merged forward into #11-#14 (merge commits, no force-push).
- 2026-11-04: F1-F4 provisional branches built and pushed (each an ACTION accept-or-revert). F2 and F3 both edit the pending-rule sets in tests/test_eligibility_others.py and tests/test_eligibility_siblings.py: whichever merges second needs a small conflict resolution (union of the sets). F1/F3 bump the profile version (v4, v5); F2 and F4 do not.
- 2026-11-04: Stage E built (PR #10); S7 re-read via Firecrawl; agent reviews: scope by visa mission (EU condition unsourced, dropped), stale rules no longer hide funds, id-collision guard; CI list 398 passed, frontend built. Stages A-E done.
- 2026-11-04: Stage D built (PR #9); S10 and S11 re-read via Firecrawl for exact deadline lines (KIT CDS has separate German/EU dates); TU Berlin S1 not encoded (not a registry source); agent reviews: group pass-through and intake/condition fixes; CI list 375 passed.
- 2026-11-04: Stage C built (PR #8); agent reviews led to stale-rule reporting, reviewer split, stricter validator; settings.yaml left unchanged because it is hash-locked as a Phase 4 input (ACTION 12f); CI list 347 passed.
- 2026-11-04: Stage B built (PR #7); agent reviews found a negated-check gap and a path-typo gap behind "none", both fixed with tests; CI list 330 passed.
- 2026-11-04: Session start: handoff files restored, baseline green (above). Stage A built (PR #5) with spec, adversary and consistency reviews (agent reviews, not human verification); fixes applied: typed area summaries, headline/admission consistency validator, closed counts keys, hash docstring. `--check-cache` flag added (PR #4).
- 2026-11-04: Source-check sheet written (S1-S15); vague session branch deleted locally (no unique commits; remote ref already gone); next-build list and open decisions recorded.
- 2026-11-04: Reviewed the pasted worksheet against the plan and merged rules (no engine run); not frozen.
- 2026-11-02: Step 3 decisions applied (accept all except D14, corrected); 70 rules `human`; PR #3 merged by the maintainer.
- 2026-10-29: Phase 6 Step 3 batch written; Steps 1-2 built; TUM Informatics rules.
- 2026-10-27: Phase 6 Step 0 inventory drafted.
- 2026-10-26: Phase 4 committed (`b85ae75`); merged later as PR #1 and #2.
- 2026-10-13 and earlier: Phases 1-3 built; Phase 6 moved before Phase 5; scope Germany only.
