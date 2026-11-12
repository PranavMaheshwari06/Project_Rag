import json

from evaluation.retrieval_eval import GoldItem, load_gold
from scripts.validate_gold import validate

REG = {"de/tum/x/page"}
SECTIONS = {"de/tum/x/page": {"Admission > Language requirements"}}
TEXTS = {"de/tum/x/page": "IELTS 6.5 or TOEFL 88. Fee 6,000 EUR."}


def item(**kw):
    return GoldItem(**({"qid": "a", "question": "q", "relevant_doc_ids": ["de/tum/x/page"]} | kw))


def test_good_items_pass():
    ok = [item(relevant_sections=["language"], answer_hint="IELTS 6.5, fee 6000",
               evidence=[{"doc_id": "de/tum/x/page", "quote": "IELTS 6.5 or\n TOEFL 88."}]),
          item(qid="r", kind="refusal", relevant_doc_ids=[], expect_refusal=True)]
    assert validate(ok, REG, SECTIONS, TEXTS) == []


def test_each_rule_fails():
    bad = [item(), item(),  # duplicate qid
           item(qid="k", kind="trivia"),
           item(qid="d", relevant_doc_ids=["de/nope"]),
           item(qid="s", relevant_sections=["deadlines"]),
           item(qid="n", answer_hint="IELTS 7.0"),
           item(qid="c", kind="coverage"),
           item(qid="w", reviewed_by="robot"),
           item(qid="e", evidence=[{"doc_id": "de/tum/x/page", "quote": "IELTS 7.0"}]),
           item(qid="o", evidence=[{"doc_id": "de/other", "quote": "IELTS 6.5"}])]
    errs = validate(bad, REG, SECTIONS, TEXTS)
    for qid in ("a", "k", "d", "s", "n", "c", "w", "e", "o"):
        assert any(e.startswith(f"{qid}:") for e in errs), qid


def test_old_format_loads_with_defaults(tmp_path):
    p = tmp_path / "g.jsonl"
    p.write_text(json.dumps({"qid": "q", "question": "?", "relevant_doc_ids": ["d"]}) + "\n")
    g = load_gold(p)[0]
    assert (g.kind, g.author, g.reviewed_by, g.expect_refusal) == ("requirement", "model", "model", False)
