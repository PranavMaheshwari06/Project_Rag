import json

import pytest
from fastapi.testclient import TestClient

from core.config import get_settings
from extraction import review
from extraction.extract import ProgrammeSource
from extraction.schemas import ProgramRequirements

DOC = "## Admission\n\n- A bachelor's degree with at least 180 ECTS is required.\n- IELTS 6.5 is accepted."
SRC = ProgrammeSource("Test Uni", "M.Sc. Testing", {"de/test/prog": DOC})


@pytest.fixture
def client(tmp_path, monkeypatch):
    paths = get_settings().paths
    monkeypatch.setattr(paths, "extracted_dir", str(tmp_path / "extracted"))
    monkeypatch.setattr(paths, "verified_dir", str(tmp_path / "verified"))
    monkeypatch.setattr(paths, "checked_dir", str(tmp_path / "checked"))
    monkeypatch.setattr(review, "sources", lambda: {SRC.slug: SRC})
    rec = {"university": "Test Uni", "programme": "M.Sc. Testing", "source_doc_ids": ["de/test/prog"],
           "min_total_ects": {"status": "stated", "value": 180, "doc_id": "de/test/prog",
                              "quote": "A bachelor's degree with at least 180 ECTS is required."},
           # list value: regression for flags() choking on nested models;
           # the en dash must not be read as the number 2013 (–)
           "english": {"status": "stated", "value": [{"test": "IELTS", "min_score": "6.5 – overall"}],
                       "doc_id": "de/test/prog", "quote": "IELTS 6.5 is accepted."}}
    (tmp_path / "extracted").mkdir()
    (tmp_path / "extracted" / f"{SRC.slug}.json").write_text(json.dumps({"model": "m", "record": rec}))
    return TestClient(review.app), rec, tmp_path


def test_draft_listed_and_missed_field_flagged(client):
    c, _, _ = client
    assert c.get("/api/programmes").json()[0]["status"] == "draft"
    flags = c.get(f"/api/programmes/{SRC.slug}").json()["flags"]
    assert "bachelor" in flags["degree_requirement"][0] and "min_total_ects" not in flags and "english" not in flags


def test_save_writes_verified_and_rejects_invented_quote(client):
    c, rec, tmp = client
    url = f"/api/programmes/{SRC.slug}"
    assert c.put(url, json=rec).status_code == 200
    saved = json.loads((tmp / "verified" / f"{SRC.slug}.json").read_text())
    assert ProgramRequirements.model_validate(saved["record"]).verified is True
    assert c.get("/api/programmes").json()[0]["status"] == "verified"

    rec["min_total_ects"]["quote"] = "At least 120 ECTS must be proven in mathematics"
    r = c.put(url, json=rec)
    assert r.status_code == 422 and "not found" in r.json()["detail"]


def test_cross_check_suggestion_must_pass_quote_check(client):
    c, _, tmp = client
    (tmp / "checked").mkdir()
    (tmp / "checked" / f"{SRC.slug}.json").write_text(json.dumps({"fields": {
        "min_total_ects": {"verdict": "correct"},
        "degree_requirement": {"verdict": "missed", "value": "Bachelor's degree", "doc_id": "de/test/prog",
                               "quote": "A bachelor's degree with at least 180 ECTS is required."},
        "semester_fee_eur": {"verdict": "missed", "value": 300, "doc_id": "de/test/prog",
                             "quote": "The semester fee is 300 euros."},  # not on the page
    }}))
    checks = c.get(f"/api/programmes/{SRC.slug}").json()["checks"]
    assert "invalid" not in checks["degree_requirement"]
    assert "not found" in checks["semester_fee_eur"]["invalid"]
    assert checks["min_total_ects"]["verdict"] == "correct"
