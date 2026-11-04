# Status (handoff)

Local only (gitignored; the copy of record is on branch `handoff-private`). Read this first in every session, then `docs/PROJECT_PLAN.md`.
Update it at the end of every session and at every "Commit Phase N": rewrite **Now** and **Next**, add one line to **Log**.

In progress: none. Session ended after the final audit; see Next.

## Now
- `main` = `e36c977`; nothing merged in this session (merging is the maintainer's). All work is on open PRs, listed in the table below in merge order.
- Done (not provisional): `--check-cache` flag (#4); A report summaries (#5); B explicit no GRE/GATE, profile-v2 (#7); C eval harness, `make eval-eligibility`, no dataset and no run (#8); D deadline and test-age checks, KIT deadline rules pending (#9); E visa funds rule file, funds per proof route, profile-v3 (#10); docs refresh (#6, merges last).
- Provisional (accept or revert, ACTION 12k): F1 credit unit closed choice, profile-v4 (#12); F2 not_published info rules (#11); F3 policy-B university assessment, profile-v5, four accepted rules back to pending (#13); F4 API + paste-to-fill + `make parse-profile` (#14).
- Last checks run (CI test list per branch): #10 finance 398 passed before the test-isolation fix (343 eligibility tests after); #12 400; #11 409; #13 407; #14 414; each with ruff clean, `--validate` "13 rule files OK", inventory "Phase 4 hashes unchanged", check-publish ok. Frontend built on #5 and #10.
- Maintainer actions: `docs/working/MAINTAINER_ACTIONS.md`; first three: 1 (sync without overwriting the worksheet), 2 (`--check-cache` locally), 3 (policy A/B).
- PR bodies carry a tool footer the cloud session could not remove (ACTION 12a).

## Baseline (2026-11-04, on `origin/main` e36c977, before any change)
- `ruff check .`: All checks passed!
- CI test list (ci.yml, includes tests/test_review.py): 229 passed, 1 warning
- `make eligibility ARGS="--validate"`: 13 rule files OK (2 TUM English quotes "cached page unavailable, not checked")
- `scripts/validate_phase6_inventory.py`: Step 0: 13 programmes / 221 fields; 17 pending reviews; Phase 4 hashes unchanged. Cached pages NOT checked.
- `make check-publish`: publish check: ok
- frontend: no package-lock.json, so `npm ci` refuses; `npm install && npm run build` (as CI does): built. The generated lock file was deleted, not committed.

## Branches (this session)
| Branch | Base | PR | State | Merge order | Provisional |
|---|---|---|---|---|---|
| eligibility-validate-check-cache-flag | main | #4 | open | 1 (it is merged into #9, so merge it first) | no |
| report-admission-readiness-finance-summaries | main | #5 | open | 2 | no |
| profile-explicit-no-gre-gate | report-admission-readiness-finance-summaries | #7 | open | 3 | no |
| eval-eligibility-harness | profile-explicit-no-gre-gate | #8 | open | 4 | no |
| date-logic-deadline-readiness | eval-eligibility-harness | #9 | open | 5 | no |
| finance-blocked-account-funds | date-logic-deadline-readiness | #10 | open | 6 | no |
| provisional-credit-unit-closed-choice | finance-blocked-account-funds | #12 | open | after #10, if accepted | YES (F1) |
| provisional-not-published-info-rules | finance-blocked-account-funds | #11 | open | after #10, if accepted | YES (F2) |
| provisional-university-assessment-fact | provisional-credit-unit-closed-choice | #13 | open | after #12, if accepted | YES (F3) |
| provisional-eligibility-api-profile-parse | finance-blocked-account-funds | #14 | open | after #10, if accepted | YES (F4) |
| docs-phase-6-progress | main | #6 | open | last (after every code PR) | no |

Stacking: later Phase 6 stages build on the report shape (A) and the profile version (B, E), so they form one chain A → B → C → D → E; merge in that order and retarget each PR to `main` after its base merges. Docs-only refresh goes on its own branch and merges last.

## Open decisions (maintainer)
1. **Degree-equivalence policy A or B** (ACTION 3; recommended B).
2. **`not_published` rows**: explicit info rules (recommended) or drop (ACTION 4).
3. **Credit unit**: closed choice ECTS/other (recommended) or aliases (ACTION 5).

## Next
1. Maintainer: ACTIONS 1-3 and 12a (footers), review and merge #4, #5, #7, #8, #9, #10 in that order (retarget each to `main` after its base merges), decide F1-F4 (ACTION 12k), merge #6 last.
2. Maintainer: finish the source check and freeze H01-H05 in `evaluation/datasets/eligibility_cases.jsonl` (ACTION 6) BEFORE `make eval-eligibility` runs on them.
3. Next build session (after merges): docs follow-ups for whichever F branches were accepted (list from the final audit in ACTIONS), the 35 assisted cases once their slots are approved (ACTION 9), other programmes' deadlines once sourced (ACTION 8).

## Cloud notes
- New container: `make install` (venv) first; `data/raw` is absent, so cached-page quote checks are skipped. Page reading works through the Firecrawl connector only.
- Git: commits authored as the repo owner (`-c user.name`/`user.email`), no attribution trailers, descriptive branch names, stage files explicitly, `make check-publish` before each commit, repo is private (`gh api repos/PranavMaheshwari06/Project_Rag --jq .private` = true). `gh pr create` fails (GraphQL blocked): open PRs with `gh api repos/.../pulls -X POST`.
- Reviewer sub-agents read the shared working tree: do not switch branches in `/home/user/Project_Rag` while they run (one review ran against a `git archive` copy because of that).

## Log (newest first)
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
