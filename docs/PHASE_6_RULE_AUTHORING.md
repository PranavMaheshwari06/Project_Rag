# Phase 6: writing a programme's rule file

How to turn a verified record (`data/verified/<slug>.json`) into a rule file
(`data/eligibility/rules/<slug>.json`) that the eligibility engine runs. Used for
the Step 3 batch and for every programme added later (data-only long tail).

Finished examples to imitate: `data/eligibility/rules/tum-m-sc-informatics.json`
and `data/eligibility/rules/kit-m-sc-computer-science.json`, with their tests in
`tests/test_eligibility_rules.py`.

## 1. Inputs

| What | Where |
|---|---|
| Verified record (the authority) | `data/verified/<slug>.json`, key `record` |
| Interpretation notes R01-R17, supplemental quotes E01-E42 | `docs/PHASE_6_RULE_REVIEW.md` |
| Field coverage per programme | `docs/PHASE_6_RULE_COVERAGE.md` |
| Cleaned page text | `.venv/bin/python scripts/dump_pages.py <slug>` -> `data/pages/<slug>/` (gitignored) |
| Raw pages (when cleaned text lost a section) | `data/raw/de/...` (file per doc id in `sources/manifest.json`) |
| Doc id -> official URL | `sources/registry.yaml` |

## 2. File format

```json
{
  "schema_version": "rules-v1",
  "slug": "<slug>",
  "record_sha256": "<record_hash(record)>",
  "rules": [
    {
      "id": "english",
      "label": "Proof of English: IELTS 6.5 or TOEFL iBT 88",
      "category": "admission",
      "severity": "hard",
      "check": {"type": "any_of", "children": [
        {"type": "min", "fact": "language.IELTS.overall", "value": "6.5"},
        {"type": "min", "fact": "language.TOEFL iBT.overall", "value": "88"},
        {"type": "university_review", "note": "Other proof the university may accept is not modelled."}
      ]},
      "citations": [{"doc_id": "de/x/language", "quote": "IELTS Academic with a minimum overall band score of 6.5."}],
      "reviewed_by": "pending"
    }
  ]
}
```

- `record_sha256`: `from eligibility.rules import record_hash; record_hash(json.load(open(path))["record"])`.
- Numbers are JSON strings (`"6.5"`), so they load as exact Decimals.
- Write JSON with `ensure_ascii=False`, two-space indent.
- `category`: `admission` (decides admission), `readiness` (needed later: APS, VPD,
  German for enrolment), `finance`. `severity`: `hard`, `soft`, `info` (a note
  shown to the student, e.g. "the committee assigns your modules"; never in the
  headline).
- `reviewed_by` is always `"pending"` when written. Only the maintainer's
  acceptance turns it into `"human"`; that never changes a record's verification tier.
- `label`: one plain-English sentence a non-programmer can read.

## 3. Checks (closed set)

| type | fields | meaning |
|---|---|---|
| `min` / `max` | `fact`, `value`, `strict` | numeric bound; `strict: true` fails at equality |
| `in` | `fact`, `values`, `negate` | fact is one of values. Strings compare case-insensitively, numbers by value (`"4"` equals `4.0`), bools match `true`/`false`. `@EHEA`, `@LISBON`, `@EU` are country groups. A list fact (documents) meets if any element matches |
| `when` | `when`, `then` | `then` applies only if `when` meets |
| `all_of` / `any_of` | `children` (non-empty) | groups |
| `university_review` | `note` | only the university can decide; never `meets` |
| `deadline` | `intake`, `close`, `open`, `starting_years` | apply by `close` (inclusive) for that intake; each date is `{month, day, year_offset}` from the starting year (the calendar year the term starts); `starting_years` limits dated windows to the years a page publishes. Reads the request's `as_of`, `intake`, `starting_year` |
| `blocked_account` | `min_eur` | visa funds, only in `data/eligibility/finance.json`: a lone blocked account in `funds` is compared with `min_eur` (Decimal, margin); any other route or a combination is `unknown` |
| `max_age` | `fact`, `years` | a test or certificate not older than `years` on the request's `as_of`; a year-only fact decides only when every day of that year agrees |

## 4. Profile facts (`eligibility/profile.py`)

Null means not supplied; `[]` or `0` means the student said none.

| fact path | type | note |
|---|---|---|
| `citizenships` | list of country names | |
| `degree_country`, `school_country` | country name (English short name, "India") | never substitute one for another |
| `degree_title`, `degree_completed` | str, bool | |
| `total_credits`, `credit_unit` | Decimal, str | units are not converted: pair a credit minimum with `in credit_unit ["ECTS"]` |
| `subject_credits.<area>` | Decimal | `<area>` is snake_case chosen by the rule file (`mathematics`, `theoretical_cs`, `core_courses`); list every new key in the decision list |
| `grade.obtained`, `grade.best`, `grade.passing` | Decimal | original scale |
| `grade.percent_of_best` | Decimal | obtained / best * 100; only meaningful next to a check on `grade.best` |
| `grade.class_rank_percentile` | Decimal | 10 = top 10% |
| `language.<TEST>.overall` / `.components.<Listening>` / `.grade` / `.taken_on` | | test names used so far: `IELTS`, `TOEFL iBT`, `PTE Academic`, `TOEIC`, `CAE`, `CPE`, `FCE` (Cambridge B2 First); add a new name (e.g. `TOEFL PBT`, `UNIcert`) only if no existing one fits, and list it in the decision list. A test missing from a supplied list counts as not taken |
| `english_instruction_share` | 0-100 | % of the prior programme taught in English |
| `german_level` | `A1`..`C2` | CEFR as certified; "at least C1" = `in ["C1", "C2"]` |
| `interview_passed` | bool | the target's interview actually passed (an invitation is not a pass) |
| `gre.quant` / `verbal` / `writing` and `*_percentile`, `gre.taken_on` | Decimal | scaled scores and percentiles are different facts; `gre: "none"` = no GRE |
| `gate.paper`, `gate.year`, `gate.qualified` | str, int, bool | `qualified` as reported on the scorecard; `gate: "none"` = no GATE |
| `documents` | list of keys | `aps_certificate`, `vpd`, ... |
| `funds_eur` | Decimal | a total with no proof route; the visa funds rule does not read it |
| `funds` | list of `{route, amount_eur}` | routes: `blocked_account`, `declaration_of_commitment`, `scholarship`, `education_loan`, `parental_income`, `bank_guarantee`; `[]` = no proof yet |
| `visa_country` | country name | where the student applies for the visa |

A fact path that does not exist raises an error in tests: do not invent one. If
a rule needs a fact that is missing, use `university_review` and list it as an
ENGINE-GAP (section 9).

## 5. Semantics

- Verdicts: `meets`, `does_not_meet`, `unknown`, `not_published`, `not_applicable`.
- `all_of`: one known failure fails it; all pass passes it; else unknown.
  `any_of`: one pass passes it; all known failures fail it; else unknown.
  `not_applicable` children are ignored.
- `when`: condition meets -> evaluate `then`; condition fails -> `not_applicable`;
  condition unknown -> unknown (never silently exempt).
- A `university_review` inside an `any_of` means the group can only be `meets` or
  `unknown`, never fail (other proof might be accepted). Use it in an `any_of`
  only where the page itself says other proof may be accepted.
- Margin positive = favourable; strict bounds fail at zero margin.
- Headline: any applicable hard admission rule failing ->
  `does_not_meet_published_requirements`; positive only if there is at least one
  hard admission rule, all `meets`, none `pending`; otherwise
  `needs_information_or_review`. Soft/info and readiness/finance rules never move it.
- Stale record hash -> no verdicts at all.
- In a group, the first unknown child's reason is shown.
- Unknown country-group membership is never an exemption; a country missing from
  a group counts as not exempt (test required).

## 6. Decided conventions (do not re-ask the maintainer)

- Separate the admission route alternatives from the GRE/GATE condition (KIT CS:
  degree AND selection-entry `any_of` AND GRE-by-country). An interview route
  needs `interview_passed: true`; an invitation is not a pass.
- Degree equivalence is always the university's call: a hard `university_review`.
  Consequence: no programme can reach a positive headline until the profile can
  carry "the university confirmed my degree equivalence" (open item).
- A university's aptitude/selection assessment with no computable formula is a
  hard `university_review`.
- Cambridge: grades A-C count; a certificate issued at a lower level does not.
- Age limits: use `max_age` only where the page measures age on the application date
  (it compares with `as_of`); otherwise write a hard `university_review` with a clear
  note. Deadlines are `readiness` rules with `deadline`; cite only pages in the
  registry. Skip fees.
- EEA is not a group. Write the three non-EU EEA countries (Iceland, Liechtenstein,
  Norway) next to `@EU` in the `in` values (see the RWTH Data Science GRE rule).
- The 2026 TOEFL 1-6 scale is its own test name, `TOEFL iBT (2026 scale)`; add a
  branch for it wherever a page publishes a new-scale minimum.
- A credit minimum that pairs with `credit_unit` uses `any_of[all_of[ECTS, min], all_of[not ECTS,
  university_review]]`: another unit is the university's call, never a fail.
- Rule citations may quote the cached raw page where the cleaned corpus lost text
  (TUM language page parser bug, fix deferred to Phase 5).
- Never invent a threshold. Unresolved or non-modelled items become
  `university_review`, `hard` if they could change admission.

## 7. Citations and the quote check

Every rule has at least one citation `{doc_id, quote}`. A quote passes if its
normalised words (`[a-z0-9]+`, lower-case) are a substring of a quote in the
verified record with the same doc id, or (where `data/raw` exists) of the cached
raw page text. Copy quotes character for character; shorter quotes are safer
than long ones that cross a line break or table cell boundary.

## 8. Validate and test

```bash
make eligibility ARGS="--validate"          # every rule file: hash, quotes, groups in date
make eligibility ARGS="--profile data/eligibility/examples/<p>.json --programme <slug> --as-of 2027-05-01 --intake winter --starting-year 2027"
.venv/bin/python -m pytest -q tests/test_eligibility_*.py
.venv/bin/ruff check .                      # never run ruff format on existing files
```

Tests read the real rule file through `load_ruleset(get_settings(), slug)`, run
offline, and cover: boundary values (at, just below), unknown vs fail, each
alternative route, the never-exempt-on-unknown rule, and that the headline is not
positive while a hard `university_review` remains. Assert verdicts, not reasons,
unless the child order makes the reason certain.

## 9. Decision list format

For the maintainer, who reads plain language, not JSON. One block per decision:

```
D?? | <Programme> | <rule in one plain sentence>
Source: <doc id> "<short quote>" <URL from sources/registry.yaml>
Assumed: <what the rule file assumes beyond the quote>
University decides: <what stays university_review>
Mechanical copy: yes|no   (yes = a number or list copied as published)
```

End with `ENGINE-GAP:` items (a fact or check the engine cannot express yet, and
what the student sees meanwhile) and open questions for the maintainer.
