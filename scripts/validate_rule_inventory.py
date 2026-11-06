"""Validate/render the rule inventory without providers, retrieval, or writes to product data.

Default: check committed identities, record bindings, baseline hashes and matrix.
--check-cache: additionally parse cached official snapshots and check every quote.
--render: explicitly regenerate only the Markdown review artifacts.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from extraction.schemas import ProgramRequirements  # noqa: E402
from ingestion.registry import load_registry  # noqa: E402

FIELDS = tuple(k for k in ProgramRequirements.model_fields
               if k not in {"university", "programme", "source_doc_ids", "verified"})
CLASSES = {"automatic", "informational_readiness", "manual_review", "not_published"}
ROOT = Path(__file__).resolve().parent.parent
INVENTORY = Path("data/eligibility/coverage_inventory.json")
MATRIX = Path("docs/eligibility-rule-coverage.md")
REVIEW = Path("docs/eligibility-rule-review.md")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_hash(record: dict) -> str:
    return digest(json.dumps(record, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False).encode("utf-8"))


def words(text: str) -> str:
    # Same comparison as extraction: case/punctuation/whitespace normalized.
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def validate(inventory: dict, records: dict, registry: list, manifest: dict,
             texts: dict[str, str] | None = None) -> list[str]:
    """Pure inventory/evidence checks. None means raw pages were NOT checked."""
    errors = []
    if inventory.get("schema_version") != "rule-inventory-v1":
        errors.append("unsupported inventory schema")
    if (inventory.get("status"), inventory.get("reviewed_by")) != (
            "draft_for_review", "pending"):
        errors.append("The inventory must retain pending review")
    registered = {e.id: e for e in registry}
    expected_slugs = {
        re.sub(r"[^a-z0-9]+", "-", f"{e.university} {e.programme}".lower()).strip("-")
        for e in registry if e.layer == "university" and e.programme
    }
    programmes = inventory["programmes"]
    if set(programmes) != expected_slugs or set(records) != expected_slugs:
        errors.append("programme inventory/verified files differ from registry")
    source_ids = {d for w in records.values() for d in w["record"]["source_doc_ids"]}
    if set(inventory["sources"]) != source_ids:
        errors.append("source inventory differs from verified record source identities")
    for doc_id, source in inventory["sources"].items():
        entry, receipt = registered.get(doc_id), manifest.get(doc_id, {})
        if entry is None or source["url"] != str(entry.url):
            errors.append(f"{doc_id}: source identity/URL differs from registry")
        for key, receipt_key in (("snapshot_sha256", "sha256"), ("cache_file", "file"),
                                 ("fetched_at", "fetched_at"), ("final_url", "final_url")):
            if source[key] != receipt.get(receipt_key):
                errors.append(f"{doc_id}: {key} differs from snapshot receipt")
        if texts is not None:
            if doc_id not in texts:
                errors.append(f"{doc_id}: cached source unavailable")
            elif digest(texts[doc_id].encode("utf-8")) != source["text_sha256"]:
                errors.append(f"{doc_id}: cleaned source hash changed")

    evidence, reviews = inventory["additional_evidence"], inventory["reviews"]

    def citation(quote, doc_id, label):
        if doc_id not in inventory["sources"]:
            errors.append(f"{label}: unknown source {doc_id}")
        if not isinstance(quote, str) or len(words(quote).split()) < 2:
            errors.append(f"{label}: missing/too short quote")
        elif texts is not None and words(quote) not in words(texts.get(doc_id, "")):
            errors.append(f"{label}: quote not found in {doc_id}")

    for eid, extra in evidence.items():
        citation(extra["quote"], extra["doc_id"], eid)
    for rid, review in reviews.items():
        if (review.get("status"), review.get("reviewed_by")) != ("pending", "pending"):
            errors.append(f"{rid}: draft interpretation cannot claim acceptance")
        if not review.get("proposed_interpretation") or not review.get("unresolved"):
            errors.append(f"{rid}: missing interpretation or unresolved boundary")
        for eid in review["evidence_ids"]:
            if eid not in evidence:
                errors.append(f"{rid}: unknown evidence {eid}")
        for ref in review["record_fields"]:
            slug, _, field = ref.rpartition(".")
            if slug not in programmes or field not in FIELDS:
                errors.append(f"{rid}: unknown record field {ref}")

    for slug, programme in programmes.items():
        if slug not in records:
            continue
        wrapper, entries = records[slug], programme["fields"]
        rec = wrapper["record"]
        try:
            ProgramRequirements.model_validate(rec)
        except ValueError as exc:
            errors.append(f"{slug}: invalid verified schema: {exc}")
        if programme["record_sha256"] != record_hash(rec):
            errors.append(f"{slug}: stale record binding")
        if programme["verification_tier"] != wrapper["tier"]:
            errors.append(f"{slug}: verification tier changed")
        if (programme["university"], programme["programme"]) != (rec["university"], rec["programme"]):
            errors.append(f"{slug}: programme name changed")
        if set(entries) != set(FIELDS):
            errors.append(f"{slug}: expected exactly {len(FIELDS)} requirement fields")
        for field, entry in entries.items():
            label = f"{slug}.{field}"
            if field not in FIELDS:
                continue
            original = rec[field]
            if entry["classification"] not in CLASSES:
                errors.append(f"{label}: unknown classification")
            if (entry["classification"] == "not_published") != (original["status"] == "not_published"):
                errors.append(f"{label}: not_published status changed")
            if not entry.get("note"):
                errors.append(f"{label}: missing automation boundary")
            citations = []
            if original["status"] == "stated":
                citations = [(original["quote"], original["doc_id"])] + [
                    (c["quote"], c["doc_id"]) for c in original.get("supporting_citations", [])]
            if set(entry["source_doc_ids"]) != {d for _, d in citations}:
                errors.append(f"{label}: cited source identities differ from verified field")
            for quote, doc_id in citations:
                citation(quote, doc_id, label)
            for rid in entry["review_ids"]:
                if rid not in reviews:
                    errors.append(f"{label}: unknown review {rid}")
            for eid in entry["evidence_ids"]:
                if eid not in evidence:
                    errors.append(f"{label}: unknown evidence {eid}")
                elif evidence[eid]["doc_id"] not in rec["source_doc_ids"]:
                    errors.append(f"{label}: supplemental evidence outside programme source scope")
    return errors


def validate_baseline(inventory: dict, root: Path) -> list[str]:
    """Preserve the recorded baseline inputs; never refresh a lock implicitly."""
    errors = []
    required = {f"data/verified/{s}.json" for s in inventory["programmes"]}
    required.update({"sources/registry.yaml", "sources/manifest.json",
                     "frontend/public/benchmark.json", "evaluation/results/refusal_calibration.json",
                     "data/audit/second_pass_audit.json", "evaluation/datasets/gold_qa.jsonl"})
    if not required.issubset(inventory["baseline_inputs"]):
        errors.append("baseline lock omits required baseline inputs")
    for name, expected in inventory["baseline_inputs"].items():
        path = root / name
        if not path.is_file() or digest(path.read_bytes()) != expected:
            errors.append(f"{name}: baseline changed/missing; review explicitly")
    return errors


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def source_link(inventory: dict, doc_id: str) -> str:
    return f"[{doc_id}]({inventory['sources'][doc_id]['url']})"


def render_matrix(inventory: dict) -> str:
    lines = ["# Programme rule coverage", "",
             "Snapshot of the rule inventory from 2026-10-27; the accepted rules are in data/eligibility/rules/. "
             "Generated from [coverage_inventory.json](../data/eligibility/coverage_inventory.json).", "",
             "All 13 programmes and all 17 original fields are inventoried below. "
             "Classification describes the proposed automation boundary, not implemented rules or measured coverage. "
             "See [the rule review notes](eligibility-rule-review.md).", "",
             "`automatic`: deterministic comparisons against entered evidence are possible after rule review. "
             "`manual_review`: equivalence, ambiguity or required university assessment remains. "
             "`informational_readiness`: process, document, milestone or finance information, separate from academic admission. "
             "`not_published`: the original verified field is empty; this never implies exemption. "
             "Supplemental evidence can expose omissions without changing the original status.", "",
             "Original values/quotes remain in the linked verified records. Source links identify the cached official "
             "snapshot, rather than asserting current live-page verification. Supporting citations are included. "
             "Rows with mixed behavior explain the numeric subchecks and the remaining review step.", "",
             "## Programme counts", "",
             "| Programme | Automatic | Information/readiness | Manual review | Not published |",
             "|---|---:|---:|---:|---:|"]
    total = Counter()
    for slug, programme in inventory["programmes"].items():
        counts = Counter(e["classification"] for e in programme["fields"].values())
        total.update(counts)
        lines.append(f"| {programme['university']} {programme['programme']} | " +
                     " | ".join(str(counts[k]) for k in ("automatic", "informational_readiness", "manual_review", "not_published")) + " |")
    lines += ["| **Total (221 fields)** | " + " | ".join(str(total[k]) for k in (
        "automatic", "informational_readiness", "manual_review", "not_published")) + " |", ""]
    for slug, programme in inventory["programmes"].items():
        lines += [f"## {programme['university']} — {programme['programme']}", "",
                  f"[Verified values and original quotes](../data/verified/{slug}.json); "
                  f"tier `{programme['verification_tier']}`; semantic review `pending`.", "",
                  f"Canonical record SHA-256: `{programme['record_sha256']}`.", "",
                  "| Original field | Classification | Comparison / boundary | Evidence and review |",
                  "|---|---|---|---|"]
        for field, entry in programme["fields"].items():
            refs = [source_link(inventory, d) for d in entry["source_doc_ids"]]
            refs += [f"[{e}](eligibility-rule-review.md#{e.lower()})" for e in entry["evidence_ids"]]
            refs += [f"[{r}](eligibility-rule-review.md#{r.lower()})" for r in entry["review_ids"]]
            lines.append(f"| `{field}` | `{entry['classification']}` | {cell(entry['note'])} | {'; '.join(refs) or '—'} |")
        lines.append("")
    lines += ["## Snapshot bindings", "",
              f"The inventory locks raw-byte hashes for {len(inventory['baseline_inputs'])} baseline inputs, canonical original-record hashes "
              "for 13 programmes, and raw/cleaned snapshot hashes for 42 source documents. "
              "No extraction record, verification tier, audit score, retrieval label or benchmark is changed.", "",
              "Run `make validate-rule-inventory` for identities, bindings and rendered-document consistency. "
              "Run `make validate-rule-inventory ARGS=\"--check-cache\"` locally to also validate "
              "raw/cleaned snapshot hashes and every original/supplemental quote. "
              "The default check does not claim raw-page or live-page verification. "
              "To explicitly regenerate the Markdown after editing the draft inventory, run "
              "`.venv/bin/python scripts/validate_rule_inventory.py --render`.", ""]
    return "\n".join(lines)


def render_review(inventory: dict) -> str:
    lines = ["# Rule review notes", "",
             "Interpretation notes and supporting evidence from the 2026-10-27 rule inventory; decisions are recorded in the rule files. "
             "These are interpretations of cached official evidence, not executable rules. "
             "Accepting a semantic interpretation does not promote a programme verification tier.", "",
                          "Acceptance of a conservative unknown does not resolve missing source evidence. "
             "Items involving omissions or genuine extraction errors need a separate reviewed Save-path correction; "
             "the verified record remains unchanged here.", "",
             "Record references below link the original values and quotes. Supplemental excerpts appear afterward "
             "with their cached snapshot hashes. New source collection, corrections and live verification are not "
             "claimed here. Source gaps must remain explicit in later catalogue readiness.", "",
             "| Item | Decision to review | Status |", "|---|---|---|"]
    lines += [f"| [{rid}](#{rid.lower()}) | {review['title']} | pending |"
              for rid, review in inventory["reviews"].items()]
    lines.append("")
    for rid, review in inventory["reviews"].items():
        lines += [f'<a id="{rid.lower()}"></a>', "", f"## {rid}: {review['title']}", "",
                  f"Proposed: {review['proposed_interpretation']}", "",
                  f"Unresolved / guard: {review['unresolved']}", ""]
        refs = []
        for ref in review["record_fields"]:
            slug, _, field = ref.rpartition(".")
            programme = inventory["programmes"][slug]
            refs.append(f"[{programme['university']} {programme['programme']} / {field}](../data/verified/{slug}.json)")
        lines += ["Original evidence: " + "; ".join(refs) + ".", ""]
        if review["evidence_ids"]:
            lines += ["Supplemental evidence: " + ", ".join(f"[{e}](#{e.lower()})" for e in review["evidence_ids"]) + ".", ""]
        lines += ["Review: **pending** · reviewer: **pending**.", ""]
    lines += ["## Supplemental cached evidence", "",
              "Excerpts use the same word-normalized quote check as extraction. "
              "The complete context remains in the cached official source. "
              "Hashes identify the raw snapshots used; no live-page check is implied.", ""]
    for eid, evidence in inventory["additional_evidence"].items():
        source = inventory["sources"][evidence["doc_id"]]
        lines += [f'<a id="{eid.lower()}"></a>', "", f"### {eid}", "",
                  source_link(inventory, evidence["doc_id"]), "",
                  "> " + evidence["quote"].replace("\n", "\n> "), "",
                  f"Fetched `{source['fetched_at']}` · raw SHA-256 `{source['snapshot_sha256']}`.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cache", action="store_true")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    inventory = json.loads((ROOT / INVENTORY).read_text(encoding="utf-8"))
    records = {p.stem: json.loads(p.read_text(encoding="utf-8"))
               for p in (ROOT / "data/verified").glob("*.json")}
    registry = load_registry(ROOT / "sources/registry.yaml")
    manifest = json.loads((ROOT / "sources/manifest.json").read_text(encoding="utf-8"))
    texts, errors = None, validate_baseline(inventory, ROOT)
    if args.check_cache:
        from core.config import get_settings
        from extraction.extract import collect_sources

        settings = get_settings()
        texts = {d: text for source in collect_sources(settings) for d, text in source.docs.items()}
        for doc_id, source in inventory["sources"].items():
            path = settings.resolve(settings.paths.raw_dir) / source["cache_file"]
            if not path.is_file() or digest(path.read_bytes()) != source["snapshot_sha256"]:
                errors.append(f"{doc_id}: raw cache hash changed/missing")
    errors += validate(inventory, records, registry, manifest, texts)
    if not errors:
        for path, content in ((MATRIX, render_matrix(inventory)), (REVIEW, render_review(inventory))):
            if args.render:
                (ROOT / path).write_text(content, encoding="utf-8")
            elif not (ROOT / path).exists() or (ROOT / path).read_text(encoding="utf-8") != content:
                errors.append(f"{path}: rendered document differs; use --render after review")
    if errors:
        print("\n".join(errors))
        return 1
    count = sum(len(p["fields"]) for p in inventory["programmes"].values())
    print(f"Inventory: {len(records)} programmes / {count} fields; "
          f"{len(inventory['reviews'])} pending reviews; baseline hashes unchanged.")
    print("Cached hashes and original/supplemental quotes checked; no live-page verification."
          if args.check_cache else "Cached pages NOT checked (use --check-cache locally); no live-page verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
