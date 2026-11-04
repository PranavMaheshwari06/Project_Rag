"""Run eligibility cases through the engine and compare with their labels
(plan section 7). Agreement is against labels written from sources, so it is a
comparison with entered facts, not an official admission verification.

Metrics: headline and criterion agreement, false-positive headlines (engine
says "meets" where the label does not), automatic-check coverage (share of
applicable hard and soft criteria the engine decided), unknown reasons, per-programme counts,
the human/assisted split, latency and the hashes of every input."""

import hashlib
import json
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
    verdicts = {c.rule_id: c.verdict for c in report.criteria}
    criteria = [
        {"rule_id": e.rule_id, "expected": e.verdict, "engine": verdicts.get(e.rule_id),
         "agree": verdicts.get(e.rule_id) == e.verdict}
        for e in case.expected_criteria
    ]
    return {
        "case_id": case.case_id,
        "slug": case.slug,
        "author": case.author,
        "expected_headline": case.expected_headline,
        "engine_headline": report.headline,
        "headline_agree": report.headline == case.expected_headline,
        "criteria": criteria,
    }


def _latency(ms: list[float]) -> dict:
    if not ms:
        return {"p50": None, "p95": None, "max": None}
    ordered = sorted(ms)
    return {"p50": statistics.median(ordered), "p95": ordered[round(0.95 * (len(ordered) - 1))], "max": ordered[-1]}


def run_cases(cases: list[EligibilityCase], settings: Settings, dataset_path: Path | None = None) -> dict:
    """Engine output never feeds back into a label: labels are read, compared, reported."""
    groups = load_groups(settings.paths.country_groups_path)
    rows, reports, latencies, programmes = [], [], [], {}
    for case in cases:
        rules, stale = load_ruleset(settings, case.slug)
        tier = record_tier(settings, case.slug)
        start = time.perf_counter()
        report = check_eligibility(case.profile, rules, stale, as_of=case.as_of, groups=groups, tier=tier)
        latencies.append((time.perf_counter() - start) * 1000)
        programmes[case.slug] = {"ruleset_sha256": ruleset_hash(rules), "record_sha256": rules.record_sha256,
                                 "rules_stale": stale, "tier": tier}
        rows.append(_compare(case, report))
        reports.append(report)
    # hard and soft criteria that apply, as counted in the report summaries
    applicable = [c for r in reports for c in r.criteria if c.verdict != "not_applicable" and c.severity != "info"]
    metrics = _agreement(rows)
    metrics["automatic_check_coverage"] = {
        "decided": sum(c.verdict in ("meets", "does_not_meet") for c in applicable),
        "applicable": len(applicable),
        "rate": sum(c.verdict in ("meets", "does_not_meet") for c in applicable) / len(applicable) if applicable else None,
    }
    metrics["unknown_reasons"] = dict(Counter(c.reason or "unspecified" for c in applicable if c.verdict == "unknown"))
    metrics["per_programme"] = {
        slug: {"cases": sum(r["slug"] == slug for r in rows),
               "headline_agree": sum(r["headline_agree"] for r in rows if r["slug"] == slug)}
        for slug in sorted({r["slug"] for r in rows})
    }
    metrics["by_author"] = {a: _agreement([r for r in rows if r["author"] == a]) for a in ("human", "assisted")}
    metrics["latency_ms"] = _latency(latencies)
    return {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "note": "Agreement with labels written from the cited sources; not an official admission verification.",
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
