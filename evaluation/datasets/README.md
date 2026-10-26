# Gold QA set

`gold_qa.jsonl` is the study-abroad gold set used by `make eval`: 104 items,
one JSON object per line. `tests/fixtures/gold_qa.jsonl` is a separate, small
fixture for the test corpus only; the tests never read this file.

## Format

| field | required | default | meaning |
|---|---|---|---|
| `qid` | yes | | stable, unique id |
| `question` | yes | | the query as a student would type it, not copied from the page |
| `relevant_doc_ids` | yes | | registry doc ids that answer it; `[]` for refusal and coverage items. Relevance is judged at doc level so labels survive re-chunking |
| `relevant_sections` | no | `[]` | lowercase substrings that must appear in a chunk's `section_path`, to narrow relevance inside a doc |
| `answer_hint` | no | `""` | what a correct answer should say; for review, not used by the retrieval metrics |
| `kind` | no | `requirement` | one of the kinds below |
| `university` | no | `null` | university name as in the registry (e.g. `TUM`), for per-university splits |
| `programme` | no | `null` | programme name as in the registry (e.g. `M.Sc. Informatics`), for per-programme splits |
| `author` | no | `model` | who wrote the question: `model` or `human` |
| `reviewed_by` | no | `model` | who last checked the label: `model` or `human` |
| `expect_refusal` | no | `false` | `true` when the system should decline (refusal and coverage items) |

The defaults live in `GoldItem` in `evaluation/retrieval_eval.py`, so an older
file with only the first five fields still loads.

## Kinds

| kind | count | what it tests |
|---|---|---|
| `requirement` | 45 | a programme requirement stated on one page (grade, credits, tests, deadlines, fees, documents) |
| `country_rules` | 24 | national rules: APS, uni-assist, visa, blocked account, insurance, residence and work permits |
| `confusable` | 11 | two sibling programmes whose pages read alike; retrieval must find the right one |
| `multi_hop` | 10 | the answer needs two docs |
| `refusal` | 9 | the corpus does not answer it; the system should decline |
| `coverage` | 5 | an uncovered university or another country; the system should say it is not covered |

## Labels

- `author` and `reviewed_by` record who wrote each item and who last checked
  its label, so the split between model and human work is visible per item
  and metrics can be reported on the human-reviewed subset.
- Current state: all 104 items are `author: model` and `reviewed_by: model`.
  The human pass is pending.
- `expect_refusal: true` marks the 14 refusal and coverage items. They have
  `relevant_doc_ids: []`, so the retrieval metrics (Recall@k, MRR, nDCG) skip
  them; they are used to calibrate the refusal threshold.

## How it was built

Questions were drafted by a model in student voice from the verified pages, in
four groups, and merged (107 items). A separate model review pass then checked
every item against its doc: 81 unchanged, 23 fixed, 3 dropped, leaving 104.
The per-item record of that pass is `gold_review.md`.

The human pass: skim `gold_review.md`; for each item, check that the listed
doc really answers it and is the only doc that does, that the hint is
supported, that the question does not copy the page's wording and that the
kind is right; accept, edit or drop; set `reviewed_by: human` on accepted
items. Items written by hand get `author: human`.

## Validator

```bash
.venv/bin/python scripts/validate_gold.py [file]   # default: this file
```

`make eval` runs it first. It exits 1 on:

- a duplicate `qid`;
- an unknown `kind`;
- `author` or `reviewed_by` not `model` or `human`;
- a doc id not in `sources/registry.yaml`, or with no chunks (run `make ingest`);
- a `relevant_sections` substring that matches no `section_path` of its docs;
- a number in `answer_hint` that is not in the doc text;
- a refusal or coverage item with doc ids, or any other item without them.
