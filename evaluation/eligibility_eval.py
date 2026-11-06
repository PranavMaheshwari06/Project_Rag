"""Run eligibility cases through the engine and compare with their labels
(plan section 7). Agreement is against labels written from sources, so it is a
comparison with entered facts, not an official admission verification.

Metrics: headline and criterion agreement, false-positive headlines (engine
says "meets" where the label does not), automatic-check coverage, unknown
reasons, per-programme counts, author and reviewer splits, latency and the
hashes of every input. Related variants of a base case are counted as cases but
not as independent observations (`independent_cases`)."""

import hashlib
import json
import math
import statistics
import time
from collections import Counter
from pathlib import Path

from core.config import Settings
from eligibility.engine import check_eligibility
from eligibility.groups import load_groups
from eligibility.report import Report
from eligibility.rules import load_ruleset, record_tier, ruleset_hash
from evaluation.eligibility_dataset import DATASET_SCHEMA_VERSION, EligibilityCase

POSITIVE = "meets_checked_published_requirements"
COVERAGE_NOTE = (
    "automatic_check_coverage counts every applicable hard and soft criterion of every case's report "
    "(admission, readiness and finance; related variants included); decided = meets or does_not_meet"
)


def _rate(agree: int, total: int) -> dict:
    return {"agree": agree, "total": total, "rate": agree / total if total else None}


def _agreement(rows: list[dict]) -> dict:
    expected = [e for r in rows for e in r["criteria"]]
    return {
        "cases": len(rows),
        "headline_agreement": _rate(sum(r["headline_agree"] for r in rows), len(rows)),
        "criterion_agreement": _rate(sum(e["agree"] for e in expected), len(expected)),
        "false_positive_headlines": sum(
            r["engine_headline"] == POSITIVE and r["expected_headline"] != POSITIVE for r in rows
        ),
    }


def _compare(case: EligibilityCase, report: Report) -> dict:
    found = {c.rule_id: c for c in report.criteria}
    criteria = []
    for e in case.expected_criteria:
        c = found.get(e.rule_id)
        criteria.append({
            "rule_id": e.rule_id,
            "expected": e.verdict,
            "engine": c.verdict if c else "absent",  # absent: stale rules give no criteria
            "engine_reason": c.reason if c else None,
            "agree": c is not None and c.verdict == e.verdict,
        })
    return {
        "case_id": case.case_id,
        "slug": case.slug,
        "author": case.author,
        "reviewer": case.reviewer,
        "related_to": case.related_to,
        "rules_stale": report.rules_stale,
        "expected_headline": case.expected_headline,
        "engine_headline": report.headline,
        "headline_agree": report.headline == case.expected_headline,
        "criteria": criteria,
        "rationale": case.rationale,
    }


def _latency(ms: list[float]) -> dict:
    if not ms:
        return {"p50": None, "p95": None, "max": None}
    ordered = sorted(ms)
    return {"p50": statistics.median(ordered), "p95": ordered[math.ceil(0.95 * len(ordered)) - 1], "max": ordered[-1]}


def run_cases(cases: list[EligibilityCase], settings: Settings, dataset_path: Path | None = None) -> dict:
    """Engine output never feeds back into a label: labels are read, compared,
    reported. Call `validate_cases` first; this function does not re-validate."""
    groups = load_groups(settings.paths.country_groups_path)
    rows, reports, latencies, programmes = [], [], [], {}
    for case in cases:
        rules, stale = load_ruleset(settings, case.slug)
        tier = record_tier(settings, case.slug)
        start = time.perf_counter()
        report = check_eligibility(case.profile, rules, stale, as_of=case.as_of, groups=groups, tier=tier,
                                   intake=case.intake, starting_year=case.starting_year)
        latencies.append((time.perf_counter() - start) * 1000)
        programmes[case.slug] = {"ruleset_sha256": ruleset_hash(rules), "record_sha256": rules.record_sha256,
                                 "rules_stale": stale, "tier": tier}
        rows.append(_compare(case, report))
        reports.append(report)
    # hard and soft criteria that apply, as counted in the report summaries
    applicable = [c for r in reports for c in r.criteria if c.verdict != "not_applicable" and c.severity != "info"]
    decided = sum(c.verdict in ("meets", "does_not_meet") for c in applicable)
    metrics = _agreement(rows)
    metrics["independent_cases"] = sum(r["related_to"] is None for r in rows)
    metrics["automatic_check_coverage"] = {
        "decided": decided, "applicable": len(applicable), "rate": decided / len(applicable) if applicable else None,
    }
    unknown = Counter(c.reason or "unspecified" for c in applicable if c.verdict == "unknown")
    unknown.update({"rules_stale": sum(r.rules_stale for r in reports)} if any(r.rules_stale for r in reports) else {})
    metrics["unknown_reasons"] = dict(unknown)
    metrics["not_published"] = sum(c.verdict == "not_published" for c in applicable)
    metrics["per_programme"] = {
        slug: _agreement([r for r in rows if r["slug"] == slug]) for slug in sorted({r["slug"] for r in rows})
    }
    all_slugs = sorted(p.stem for p in Path(settings.paths.rules_dir).glob("*.json"))
    metrics["programmes_without_cases"] = [s for s in all_slugs if s not in programmes]
    metrics["by_author"] = {a: _agreement([r for r in rows if r["author"] == a]) for a in ("human", "assisted")}
    metrics["by_reviewer"] = {
        str(v): _agreement([r for r in rows if r["reviewer"] == v]) for v in ("human", "model", None)
    }
    metrics["latency_ms"] = _latency(latencies)
    return {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "note": "Agreement with labels written from the cited sources; not an official admission verification.",
        "coverage_note": COVERAGE_NOTE,
        "metrics": metrics,
        "disagreements": [r for r in rows if not r["headline_agree"] or not all(e["agree"] for e in r["criteria"])],
        "hashes": {
            "dataset_sha256": hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest() if dataset_path else None,
            "country_groups_sha256": hashlib.sha256(Path(settings.paths.country_groups_path).read_bytes()).hexdigest(),
            "programmes": programmes,
        },
    }


def write_results(results: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
