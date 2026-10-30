# Engineering decisions

Dated log of the calls I made while building this, and why. Newest last.

## 2026-07-24 — custom modules over LangChain/LlamaIndex

Framework RAG hides exactly the things this project exists to show: where
candidates come from, how they're fused, why a chunk won. Writing the ~6
retrieval modules by hand cost maybe a day and means every score in the trace
is explainable. I'd reconsider for a team that needs 20 loaders, not for this.

## 2026-07-25 — structure-aware chunking, whitespace token proxy

Fixed-size chunking chops code examples in half, and half a code block is
worse than none — it looks authoritative and runs into a syntax error.
So: split on headings, pack to 512–1024 tokens, never break a fenced block,
carry ~12% word-level overlap. I count tokens by whitespace instead of BPE;
it's within ~25% on prose, and the budget doesn't need to be exact — it needs
to be consistent. Not worth a tiktoken dependency.

*Updated 2026-10-07: the proxy alone did not hold on this corpus. German text
and tables run up to 2.7 model tokens per word, so 16 of 398 chunks overflowed
bge-small's 512-token limit. The proxy still does the packing (current
settings: 256 target / 384 max whitespace words), and a second pass with the
embedder's own tokenizer re-splits any chunk over 510 tokens. See the
2026-10-07 entry below.*

## 2026-07-26 — RRF over weighted score fusion

Dense cosine lives in [0,1]-ish, BM25 is unbounded and corpus-dependent.
Weighted sums need per-corpus score normalization that quietly rots when the
corpus changes. RRF only consumes ranks, has one parameter (k=60, straight
from the Cormack et al. paper), and is deterministic with a lexical
tie-break. Slightly worse than a perfectly tuned weighted fusion in papers;
massively better than a badly tuned one in practice.

## 2026-07-27 — memory vector store first, Qdrant behind the same interface

Local-first constraint for this phase: no containers. Brute-force cosine over
a NumPy matrix is exact (not ANN-approximate), ~instant at this corpus size,
and persists as one .npz file. The Qdrant implementation sits behind the same
build/load/search interface and is selected by `vector_backend` in
settings.yaml, so the swap is config, not code. The interface is three
methods precisely so both backends stay honest.

## 2026-07-28 — bge-small for embeddings, bge-reranker-base for rerank

bge-small-en-v1.5: 384 dims, ~130MB, strong retrieval scores for its size,
tolerable on CPU. The reranker is the expensive piece (~1.1GB, cross-encodes
query×chunk), so it only sees the top rerank_n=10 fused candidates — that's
the latency budget: rerank cost is capped by a config knob, not by corpus
size. I force a sigmoid on the reranker logits so the refusal threshold in
config compares against a stable 0..1 scale regardless of library defaults.

## 2026-07-29 — refuse on weak evidence, threshold on the rerank score

The refusal gate uses the *reranker's* top score, not cosine similarity —
cosine against an embedded query is always "somewhat high" for in-domain
vocabulary, while a cross-encoder actually reads the pair and scores garbage
near zero. Threshold 0.3 chosen by eyeballing scores for on-corpus questions
(consistently >0.9) vs off-corpus ones (<0.05). It's a config knob because
that gap will narrow on messier corpora.

*Updated 2026-10-26: those scores came from the earlier technical-documentation
corpus. The threshold is recalibrated on this corpus in Phase 4 (step 4) with
the 14 refusal and coverage probes in the gold set; not done yet.*

## 2026-07-30 — doc-level gold labels, not chunk ids

First draft labeled relevant chunk_ids. Then I changed the chunker config and
every label rotted. Relevance is now judged at doc level with optional
section-path substrings to narrow it; labels survive re-chunking, which is
the thing you tune most. The tradeoff: recall against doc-level labels is
easier to saturate on a small corpus — noted in the README limitations.

*Updated 2026-10-26: still in force. This corpus showed the opposite cost as
well: when the same fact is stated on two pages, a one-doc label undercounts
recall. Gold items with that problem were reworded or dropped (3 dropped).*

## 2026-07-31 — extractive fallback instead of a mocked LLM

No API key must still mean a working demo, but faking an LLM response would
poison the groundedness numbers. The fallback selects the most query-relevant
prose sentences from each evidence chunk and cites them — dumb, honest, and
grounded by construction. It shares evidence numbering with the LLM path so
the citation mapper and its tests cover both.

## 2026-08-01 — groundedness by token overlap, clearly labeled

An LLM-judge without a key is a mock, and inventing metrics is worse than
crude ones. The overlap heuristic (≥50% of a claim's content words present in
cited evidence) is labeled "token-overlap heuristic (not an LLM judge)" in
the benchmark JSON, the dashboard, and the README. When a key is available,
an LLM judge can slot into answer_eval.py without touching the harness.

## 2026-10-05 — crawl separate from ingest, robots.txt fails closed, bot walls dropped

The corpus is a few dozen official pages spread over DAAD, uni-assist, APS,
BAMF, embassies and university sites. `make crawl` is the only network step:
it downloads each registry URL once into `data/raw/` and writes a receipt per
page (hash, redirects, error) to `sources/manifest.json`. Parsing, chunking
and indexing are offline and re-run in seconds, which matters because they
are what I tune; downloading is slow, flaky and rude to repeat. If robots.txt
cannot be read (unreachable, 401/403, 5xx) the crawler treats the site as
disallowed, because a tool that cites official sources should not guess
permission. Sites behind a bot wall are dropped, not worked around: Make it in
Germany showed one, so BAMF and Service Berlin cover the same rules. No
per-site scrapers either; I keep the whole page as text so a redesign does not
break extraction. The cost: fail-closed skipped Deutschlandstipendium once on
a transient robots.txt error (fetched on retry), and I lost one well-written
source.

## 2026-10-06 — Germany only; batch 2 before the eval baseline; agent before deploy, MCP after

I dropped the UK and US. Germany is where I study, so I can check the sources
and edge cases myself, and its admission system (uni-assist, APS, grade
conversion, blocked account) is rule-based, which fits a deterministic rules
engine. Every programme record has to be verified, so one country done well
beats three done badly. The pilot is 5 universities; more universities land at
the end of Phase 3, before the evaluation baseline, so the gold set, the
ablations and the demo all run on the corpus that ships. The small agent stays
in Phase 7, before deploy, because the live demo needs it. The MCP server moves
to Phase 11, after deploy: it exposes the agent's tools, so it is a thin layer
once those exist, and nothing in the demo depends on it. The trade-off is
reach: students looking at other countries get a "Germany only" answer and a
portal link.

*Updated 2026-10-13: batch 2 was cut from about seven universities to three;
see the 2026-10-13 entry.*

## 2026-10-07 — chunk limit checked with the real tokenizer

After the first ingest, 16 of 398 chunks were longer than bge-small's
512-token limit and lost their tails silently at embedding time. German text
and tables run up to 2.7 model tokens per word, so the whitespace proxy from
2026-07-25 undercounts exactly where the facts are (fee tables, deadlines).
I kept the proxy for packing and added a second pass: every chunk is counted
with the embedder's own tokenizer and any chunk over
`chunking.model_token_limit` (510) is re-split. Result: 415 chunks, 0
truncated, with a test for it. The tokenizer comes with the embedding model
I already load, so it adds no dependency; ingest now has to load it.

## 2026-10-07 — Gemini free tier through its OpenAI-compatible endpoint

There is no paid LLM budget. I chose the Gemini free tier on 2026-10-05 and
wired it on 2026-10-07 through Gemini's OpenAI-compatible endpoint, using the
OpenAI SDK in one thin client (`generation/llm_client.py`), so the provider is
a `base_url` and a model name in `config/settings.yaml`, not code.
`gemini-2.5-flash` was closed to new keys, so the default is
`gemini-3.8-flash`; on 2026-10-13 I added a fallback list
(`gemini-3.6-flash`, `gemini-3.5-flash`) that a 429 moves through. The costs
are real: about 20 requests a day per model, about a minute per extraction
call and occasional 503s, so extraction is resumable and the deployed chat
will need caching. Free-tier prompts may be used by the provider, so no real
personal profiles go through it.

## 2026-10-07 — every extracted field is Cited: a stated value with a quote, or not_published

Each field of `ProgramRequirements` (17 now) is either `stated` with a value,
a verbatim quote and the doc id it came from, or `not_published`. The quote
lets a person verify a field in seconds, and it lets code reject a value the
model invented: a field whose quote (word-normalised, at least 2 words) is not
in the cited page is dropped. `not_published` is a real answer that the rules
engine will turn into "unknown", never a guess. English scores stay as text
(6.5, 88, C1) because each test has its own scale; conversion belongs to the
engine. The limit: a passing quote check proves the words are on the page,
not that the value was read correctly (scope, conditions, who it applies to).
That is what the cross-check and review are for, and the schema still cannot
express some rules (the schema gaps in LEARNING.md).

## 2026-10-13 — second-model cross-check plus a human tick; cross-checks committed

A model from a different family reads each draft and the exact page text and
gives a verdict per field (correct, wrong, partial, missed, not_published_ok,
unsure), with an optional fix. Models from the same family tend to make the
same mistakes; a different family's errors overlap less. The checker can be
wrong too, so a suggested fix must pass the same schema and quote check or the
review screen marks it invalid. The screen shows each field green (checker
agrees, no warning) or amber, so reading time goes where the risk is, and a
person ticks every field before Save. On 2026-10-16 I decided to commit
`data/checked/` next to the drafts and verified records: together they are the
audit trail, and they are the inputs for the Phase 4 accuracy numbers. The
cross-check runs offline over local files, not through a paid API. Trade-offs:
the reviewer sees the checker's verdict, so checker precision is not measured
independently; and a check file does not record which draft it checked, so it
must be re-run after every re-extraction.

*Updated 2026-10-23: the hand tick held for six programmes; the other seven
were verified by a second pass (entry below).*

## 2026-10-13 — batch 2 is KIT, TU Darmstadt and Stuttgart; Phase 6 before Phase 5; plain UI before deploy

The goal is a deployed system soon, and each programme costs about 30 minutes
of verification plus free-tier quota. So batch 2 is three universities, five
programmes: KIT (CS, Computational and Data Science), TU Darmstadt (CS, AI and
Machine Learning) and Stuttgart (CS only; its AI / Data Science master's is
German-taught). LMU, Bonn, Tübingen and Mannheim were cut; adding them later
is data work, not code. The eligibility engine (Phase 6) moves before the
retrieval upgrades (Phase 5): the engine is the product and needs only the
verified records, while retrieval upgrades need the Phase 4 baseline to be
judged. Phase 9 becomes a plain, working UI with no animation, and visual
polish moves to Phase 12, after deploy, because a working live URL matters
more than motion. The cost: fewer programmes at launch, and fewer look-alike
programme pages to stress the retrieval filters.

## 2026-10-23 — the remaining seven programmes verified by a second pass, not a hand tick

Six programmes were ticked field by field in the review screen. To ship
sooner, the other seven (KIT CDS, Saarland CS, TU Darmstadt AIML, TU Dresden
CS, TUM DEA, TUM Informatics, Stuttgart CS) were verified by a second,
model-assisted pass that re-read every field against its cited pages, with no
outside knowledge, and saved through the review screen's Save path, so the
schema and quote-in-page checks still applied. The first record was checked
against its pages before the rest ran, and four calls were reverted after
re-reading the pages. Rules that came out of it: an example ("e.g. TOEFL 95")
is not a minimum; a list is stated only if the page gives the list; an
inference is not stated unless the page says it; a date is not tagged with an
applicant group the page does not name. This relaxes "every field is ticked by
hand" for these seven. The cost: for them, the verified record and the
cross-check are not independent, so the Phase 4 draft-vs-verified and checker
numbers are headlined on the six hand-verified programmes.

## 2026-10-26 — verification tiers and a sampled audit instead of hand-ticking all 13

Hand-ticking the seven second-pass records would cost about 30 minutes each.
Instead each `data/verified/<slug>.json` now carries a `tier`: `human` (6
programmes, every field ticked in `make review`) or `second_pass` (the 7
above). A re-save keeps the existing tier; promoting `second_pass` to `human`
is a deliberate hand edit, so the label cannot drift upward by accident. To
put a number on second-pass quality, `scripts/audit_sample.py 35 4 --sheet`
draws a seeded sample of 35 of the 69 stated fields in second-pass records and
writes an audit sheet (value, quote, page excerpt, a model pre-check line, an
agree/disagree box). The pre-check agreed on 33 and disagreed on 2. The human
audit is pending; its result goes to `data/audit/second_pass_audit.json`, and
confirmed errors are fixed through the Save-path quote check while the tier
stays `second_pass`. Why: ship sooner and keep every claim about the data
honest. The trade-off is statistical: a sample gives an estimate with an
interval, and zero errors in 35 still allows an error rate up to about 10%
(Wilson 95%). Only stated fields are sampled, so missed fields are not
estimated.

## 2026-10-26 — synthetic profiles move from Phase 4 to Phase 6

The ~40 synthetic profiles test eligibility verdicts, and the engine that
produces verdicts does not exist yet. Writing expected verdicts now would
mean guessing how open schema gaps (for example a conditional entrance exam)
will be modelled, then rewriting them. They move to Phase 6, next to the
engine they test. The cost: the Phase 4 baseline covers retrieval and
extraction only; eligibility accuracy is reported in Phase 6.

## 2026-10-26 — gold set: model-assisted, human-reviewed, with author and reviewed_by per item

The gold set (`evaluation/datasets/gold_qa.jsonl`, 104 items) was drafted by
a model as student-voice questions from the verified pages, then a separate
model review pass checked every item against its doc (107 drafted: 81
unchanged, 23 fixed, 3 dropped). `scripts/validate_gold.py` checks every label
mechanically and runs before `make eval`. Drafting is the cheap part; judging
whether the label is right and the only right answer is where a person adds
value, so the human pass is review, not writing from scratch. Each item
records `author` and `reviewed_by` (model or human). Today every item is
model/model; the human review is pending. Recording it per item means the
split is visible and metrics can be reported on the human-reviewed subset. The
risks are that model-written questions echo page wording (which flatters BM25)
and that a model reviewing a model shares its blind spots; the review
checklist looks for the first, and the human pass is there for the second.

## 2026-10-26 — extraction accuracy counts value, quote and doc_id

A field counts as "draft unchanged" only if status, value, quote and doc_id
are all identical between the LLM draft and the verified record. The product
promises a citation, so a right value with a wrong quote or page is still a
correction. The headline uses the human tier only: 0.794 of 102 fields across
6 programmes survived unchanged; second-pass records were verified with the
cross-check's help, so they say nothing independent. The cost: a cosmetic
quote trim counts as an edit, so the number is conservative, and the checker's
precision and recall mean "predicts what a person who could see its verdict
changed", not an independent score.
