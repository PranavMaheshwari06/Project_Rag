# Planning and evidence index

Updated 2026-11-04. The product is a Germany master's eligibility assistant for students, and an applied AI / LLM systems engineering portfolio project for its maintainer.

## Current planning documents

| Document | What it controls |
|---|---|
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Product scope, architecture, constraints, full roadmap, phase order, manual tasks, and definition of done. This is the main project specification. |
| [PHASE_6_IMPLEMENTATION_PLAN.md](PHASE_6_IMPLEMENTATION_PLAN.md) | Detailed next-phase specification: deterministic eligibility, profiles, rule interpretation, APIs, evaluation, implementation steps, and review gates. |
| [DECISIONS.md](../DECISIONS.md) | Dated decisions and their tradeoffs, including the October 13 decision to build Phase 6 before Phase 5. Historical entries describe the state on their date; later updates record resolutions. |
| [LEARNING.md](../LEARNING.md) | What was built and measured, explanations, interview questions, and unresolved findings that implementation must carry forward. The Phase 3 schema gaps are especially relevant to Phase 6. |
| [README.md](../README.md) | Current capabilities, reproducible commands, results, and limitations for users and reviewers. It must describe implemented behavior, rather than promise unfinished features. |
| [Gold dataset README](../evaluation/datasets/README.md) | Retrieval gold labels, authorship/review provenance, validation, and the Phase 4 evaluation procedure. This dataset evaluates retrieval; it is not eligibility ground truth. |

Explicit maintainer instructions take precedence. Keep the detailed phase specification consistent with the main roadmap. Bring any conflict into the open rather than silently adding a second product direction.

## Implementation evidence and inputs

- [Phase 6 coverage matrix](PHASE_6_RULE_COVERAGE.md): Step 0 draft for all 13 programmes and 17 original fields, with source identities and preserved Phase 4 hashes in `data/eligibility/coverage_inventory.json`.
- [Phase 6 consequential rule review](PHASE_6_RULE_REVIEW.md): the Step 0 packet of semantic interpretations, exceptional-branch evidence, omissions and unresolved source gaps. The maintainer's decisions were taken in Step 3 (2026-10-29, 2026-11-02) and are recorded in LEARNING.md and in each rule's `reviewed_by`; seven reviewed-file rules remain `pending` (KIT CS degree, degree_ects, module_assignment, test_validity and English; TUM Informatics APS and VPD), plus the four KIT deadline rules and the visa funds rule added after Step 3.
- `extraction/schemas.py`: the existing 17 cited requirement fields and the Phase 4 additions for conditions, degree origin, and supporting citations.
- `data/verified/`: the 13 programme records, retaining their `human` or `second_pass` provenance. Verification does not establish automatic machine interpretability.
- `sources/registry.yaml` and `sources/manifest.json`: official source identities and cached snapshot receipts.
- `data/audit/second_pass_audit.json`: completed audit evidence, original scores, and the six corrections.
- `frontend/public/benchmark.json` and `evaluation/results/refusal_calibration.json`: Phase 4 aggregate/per-kind results, per-query diagnostics, calibration sweep, and input hashes.
- `Makefile`, `.github/workflows/ci.yml`, and `tests/`: the established run, validation, and CI conventions.

## Historical material

`REVIEW_AND_FINALIZATION_PLAN.md` is an ignored local file present in this workspace. It records the October 2 review of the old EngineerDoc prototype, including a proposed version-aware engineering-documentation product. That product direction was superseded by the Germany admissions roadmap. Its unresolved engineering findings are relevant only where the current project plan carries them forward. Its old completion statements, job-posting examples, and deployment recommendations are historical evidence, not the current specification.

## Build order and working loop

Build order: **1 → 2 → 3 → 4 → 6 → 5 → 7 → 8 → 9 → 10 → 11 → 12**.

Every phase follows the same loop: kickoff brief → small runnable implementation steps → focused checks → maintainer hands-on task → reproducible end-to-end run → explanation and learning notes → dated decision entry → phase branch and PR.

The maintainer's learning is part of the deliverable: explain the choices, independently label selected examples, and be able to demonstrate the result. Personal rewrites of decision entries and the deferred quiz batch do not gate progress.
