import json

import pytest

from core.config import get_settings
from evaluation import extraction_eval as ev
from extraction.extract import FIELDS

NP = {"status": "not_published", "value": None, "quote": None, "doc_id": None}


def st(v):
    return {"status": "stated", "value": v, "quote": "q", "doc_id": "d"}


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    paths = get_settings().paths
    for k in ("extracted", "checked", "verified"):
        monkeypatch.setattr(paths, f"{k}_dir", str(tmp_path / k))
        (tmp_path / k).mkdir()
    return tmp_path


def test_outcomes_and_checker_scores(dirs):
    tmp_path = dirs
    draft = {f: NP for f in FIELDS} | {"degree_requirement": st("B.Sc."), "min_total_ects": st(180),
                                       "german": st("B2"), "deadlines": st("x")}
    final = draft | {"min_total_ects": st(210), "german": NP, "work_experience": st("1y")}
    (tmp_path / "extracted/a.json").write_text(json.dumps({"record": draft}))
    (tmp_path / "verified/a.json").write_text(json.dumps({"tier": "human", "record": final}))
    verdicts = {"min_total_ects": "wrong", "deadlines": "partial", "german": "correct"}  # 1 hit, 1 false alarm, 2 misses
    (tmp_path / "checked/a.json").write_text(json.dumps({"fields": {k: {"verdict": v} for k, v in verdicts.items()}}))

    s = ev.summarize(ev.compare(get_settings()))
    assert s["outcomes"] == {"unchanged": len(FIELDS) - 3, "edited": 1, "dropped": 1, "added": 1}
    assert (s["checker_flagged"], s["checker_precision"], s["checker_recall"]) == (2, 0.5, round(1 / 3, 3))
    assert ev.summarize(ev.compare(get_settings()), "second_pass")["fields"] == 0


def test_quote_only_edit_counts_as_edited():
    assert ev._outcome(st(1), st(1) | {"quote": "better"}) == "edited"
    assert ev._outcome(st(1), st(1) | {"doc_id": "other"}) == "edited"


def test_bad_or_missing_tier_raises(dirs):
    draft = {f: NP for f in FIELDS}
    (dirs / "extracted/a.json").write_text(json.dumps({"record": draft}))
    for verified in ({"record": draft}, {"tier": "second-pass", "record": draft}):
        (dirs / "verified/a.json").write_text(json.dumps(verified))
        with pytest.raises(ValueError, match="tier"):
            ev.compare(get_settings())


def test_stale_check_is_ignored(dirs):
    draft = {f: NP for f in FIELDS}
    (dirs / "extracted/a.json").write_text(json.dumps({"extracted_at": "2026-10-20T00:00:00", "record": draft}))
    (dirs / "verified/a.json").write_text(json.dumps({"tier": "human", "record": draft}))
    (dirs / "checked/a.json").write_text(json.dumps({"checked_at": "2026-10-10T00:00:00",
                                                     "fields": {"german": {"verdict": "wrong"}}}))
    assert {r["verdict"] for r in ev.compare(get_settings())} == {None}
