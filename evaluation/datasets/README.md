# Gold QA set

The FastAPI seed set now lives in `tests/fixtures/gold_qa.jsonl` (test corpus
only). The study-abroad gold set is written here in Phase 4, same format,
one JSON object per line:

- `qid`: stable id
- `question`: the query as a user would type it
- `relevant_doc_ids`: doc ids that answer it (relevance is judged at doc level
  so labels survive re-chunking)
- `relevant_sections` (optional): lowercase substrings that must appear in the
  chunk's `section_path`, to narrow relevance inside a doc
- `answer_hint`: what a correct answer should say (for human review, not used
  by the metrics)

## TODO(human): expand the gold set

The current 8 seed pairs are enough to smoke-test the harness, not to draw
conclusions. Before quoting benchmark numbers anywhere:

1. Grow this file to **30–60 pairs**. Write questions the way a real user
   would ask them (short, no doc vocabulary copied verbatim).
2. Include ~5 questions the corpus **cannot** answer, marked with
   `"relevant_doc_ids": []` — useful for eyeballing refusal behaviour
   (the retrieval metrics skip them; division-by-zero guards are in place).
3. Hand-check every `relevant_doc_ids` label by actually reading the doc.
4. Re-run `make eval`.
