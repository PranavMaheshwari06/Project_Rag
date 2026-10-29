import copy
import json

import pytest

from extraction.schemas import ProgramRequirements
from ingestion.registry import RegistryEntry
from scripts.validate_phase6_inventory import (
    FIELDS,
    digest,
    record_hash,
    validate,
    validate_baseline,
)


@pytest.fixture
def inventory_fixture():
    doc_id = "de/test/programme"
    text = "A bachelor's degree with at least 180 ECTS is required."
    rec = ProgramRequirements(
        university="Test Uni", programme="M.Sc. Testing", source_doc_ids=[doc_id], verified=True,
        min_total_ects={"status": "stated", "value": 180, "quote": text, "doc_id": doc_id},
    ).model_dump(mode="json")
    slug = "test-uni-m-sc-testing"
    registry = [RegistryEntry(id=doc_id, url="https://example.edu/programme", country="de",
                              layer="university", university=rec["university"], programme=rec["programme"])]
    source = {"url": str(registry[0].url), "final_url": str(registry[0].url),
              "snapshot_sha256": "a" * 64, "text_sha256": digest(text.encode()),
              "cache_file": "de/test/programme.html", "fetched_at": "2026-10-01T00:00:00Z"}
    manifest = {doc_id: {"sha256": source["snapshot_sha256"], "file": source["cache_file"],
                         "final_url": source["final_url"], "fetched_at": source["fetched_at"]}}
    fields = {f: {"classification": "not_published", "note": "Not an exemption.",
                  "review_ids": [], "source_doc_ids": [], "evidence_ids": []} for f in FIELDS}
    fields["min_total_ects"] = {"classification": "automatic", "note": "Confirmed ECTS only.",
                                "review_ids": ["R01"], "source_doc_ids": [doc_id], "evidence_ids": ["E01"]}
    inventory = {
        "schema_version": "phase6-inventory-v1", "status": "draft_for_maintainer_review", "reviewed_by": "pending",
        "sources": {doc_id: source}, "additional_evidence": {"E01": {"doc_id": doc_id, "quote": "at least 180 ECTS"}},
        "reviews": {"R01": {"status": "pending", "reviewed_by": "pending", "proposed_interpretation": "Compare ECTS.",
                             "unresolved": "Other units require review.", "evidence_ids": ["E01"],
                             "record_fields": [slug + ".min_total_ects"]}},
        "programmes": {slug: {"university": rec["university"], "programme": rec["programme"],
                               "record_sha256": record_hash(rec), "verification_tier": "second_pass", "fields": fields}},
    }
    return inventory, {slug: {"record": rec, "tier": "second_pass"}}, registry, manifest, {doc_id: text}


def test_cached_quotes_and_snapshot_bindings_pass(inventory_fixture):
    assert validate(*inventory_fixture) == []
    # CI can check identities/bindings without pretending it checked raw pages.
    assert validate(*inventory_fixture[:4]) == []


def test_missing_programme_or_field_cannot_silently_reduce_coverage(inventory_fixture):
    inventory, records, registry, manifest, texts = inventory_fixture
    del next(iter(inventory["programmes"].values()))["fields"]["entrance_tests"]
    assert any("exactly 17" in e for e in validate(inventory, records, registry, manifest, texts))
    inventory["programmes"].clear()
    assert any("differ from registry" in e for e in validate(inventory, records, registry, manifest, texts))


def test_changed_requirement_tier_and_invented_exemption_are_detected(inventory_fixture):
    inventory, records, registry, manifest, texts = inventory_fixture
    wrapper = next(iter(records.values()))
    wrapper["record"]["min_total_ects"]["value"] = 120
    wrapper["tier"] = "human"
    next(iter(inventory["programmes"].values()))["fields"]["english"]["classification"] = "automatic"
    errors = validate(inventory, records, registry, manifest, texts)
    for expected in ("stale record binding", "verification tier changed", "not_published status changed"):
        assert any(expected in e for e in errors)


def test_source_and_quote_changes_are_detected(inventory_fixture):
    inventory, records, registry, manifest, texts = inventory_fixture
    inventory["additional_evidence"]["E01"]["quote"] = "at least 120 ECTS"
    assert any("quote not found" in e for e in validate(inventory, records, registry, manifest, texts))
    assert validate(inventory, records, registry, manifest) == []
    manifest["de/test/programme"]["sha256"] = "b" * 64
    texts["de/test/programme"] += " A new prerequisite."
    errors = validate(inventory, records, registry, manifest, texts)
    assert any("snapshot_sha256 differs" in e for e in errors)
    assert any("cleaned source hash changed" in e for e in errors)


def test_unknown_sources_and_review_ids_fail(inventory_fixture):
    inventory, records, registry, manifest, texts = inventory_fixture
    entry = next(iter(inventory["programmes"].values()))["fields"]["min_total_ects"]
    entry.update(source_doc_ids=["de/other/programme"], review_ids=["R99"], evidence_ids=["E99"])
    inventory["additional_evidence"]["E01"]["doc_id"] = "de/other/programme"
    errors = validate(inventory, records, registry, manifest, texts)
    for expected in ("source identities differ", "unknown review R99", "unknown evidence E99", "unknown source"):
        assert any(expected in e for e in errors)


def test_model_draft_cannot_claim_maintainer_acceptance(inventory_fixture):
    inventory, records, registry, manifest, texts = inventory_fixture
    inventory["reviewed_by"] = "human"
    inventory["reviews"]["R01"].update(status="accepted", reviewed_by="human")
    errors = validate(inventory, records, registry, manifest, texts)
    assert any("pending maintainer review" in e for e in errors)
    assert any("cannot claim acceptance" in e for e in errors)


def test_baseline_check_is_read_only_and_catches_artifact_drift(tmp_path, inventory_fixture):
    inventory = copy.deepcopy(inventory_fixture[0])
    names = ["data/verified/test-uni-m-sc-testing.json", "sources/registry.yaml", "sources/manifest.json",
             "frontend/public/benchmark.json", "evaluation/results/refusal_calibration.json",
             "data/audit/second_pass_audit.json", "evaluation/datasets/gold_qa.jsonl"]
    inventory["baseline_inputs"] = {}
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"original": True}))
        inventory["baseline_inputs"][name] = digest(path.read_bytes())
    assert validate_baseline(inventory, tmp_path) == []
    benchmark = tmp_path / "frontend/public/benchmark.json"
    benchmark.write_text('{"original": false}')
    assert any("benchmark.json: Phase 4 baseline changed" in e for e in validate_baseline(inventory, tmp_path))
    assert benchmark.read_text() == '{"original": false}'
    del inventory["baseline_inputs"]["data/audit/second_pass_audit.json"]
    assert any("omits required" in e for e in validate_baseline(inventory, tmp_path))
