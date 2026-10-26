"""Extraction accuracy, offline: how often the LLM draft survived human verification, and how
well the cross-check predicted the fields that changed.

Headline numbers use the `human` tier only: second_pass records were verified with the
cross-check's help, so they say nothing independent about the draft or the checker. Even on the
human tier the checker numbers mean "predicts what a person who could see its verdict changed",
because the review screen shows the verdict next to each field."""

import json
from collections import Counter
from pathlib import Path

from core.config import Settings
from extraction.extract import FIELDS

FLAGGED = {"wrong", "partial", "missed"}  # cross-check verdicts that say "the draft is off"
TIERS = {"human", "second_pass"}


def _read(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _outcome(draft: dict, final: dict) -> str:
    if draft["status"] == final["status"] == "not_published":
        return "unchanged"
    if draft["status"] == "stated" and final["status"] == "not_published":
        return "dropped"
    if draft["status"] == "not_published":
        return "added"
    same = all(draft[k] == final[k] for k in ("value", "quote", "doc_id"))  # a corrected citation is still a correction
    return "unchanged" if same else "edited"


def compare(settings: Settings) -> list[dict]:
    """One row per (programme, field): outcome, tier and the cross-check verdict."""
    p = settings.paths
    dirs = [settings.resolve(getattr(p, f"{k}_dir")) for k in ("extracted", "checked", "verified")]
    rows = []
    for vf in sorted(dirs[2].glob("*.json")):
        verified, draft = _read(vf), _read(dirs[0] / vf.name)
        if not draft:
            continue
        if verified.get("tier") not in TIERS:
            raise ValueError(f"{vf.name}: tier must be one of {sorted(TIERS)}, got {verified.get('tier')!r}")
        check = _read(dirs[1] / vf.name) or {}
        if check and check.get("checked_at", "") < draft.get("extracted_at", ""):
            print(f"warning: {vf.name} cross-check predates its draft, verdicts ignored")  # ISO strings sort by time
            check = {}
        checked = check.get("fields", {})
        for name in FIELDS:
            rows.append({
                "slug": vf.stem, "field": name, "tier": verified["tier"],
                "outcome": _outcome(draft["record"][name], verified["record"][name]),
                "verdict": checked.get(name, {}).get("verdict"),
            })
    return rows


def summarize(rows: list[dict], tier: str | None = "human") -> dict:
    rows = [r for r in rows if tier is None or r["tier"] == tier]
    outcomes = Counter(r["outcome"] for r in rows)
    flagged = [r for r in rows if r["verdict"] in FLAGGED]
    bad = [r for r in rows if r["outcome"] != "unchanged"]
    hit = [r for r in flagged if r["outcome"] != "unchanged"]
    return {
        "tier": tier or "all", "programmes": len({r["slug"] for r in rows}), "fields": len(rows),
        "outcomes": dict(outcomes),
        "draft_accuracy": round(outcomes["unchanged"] / len(rows), 3) if rows else None,
        "checker_flagged": len(flagged), "checker_unsure": sum(r["verdict"] == "unsure" for r in rows),
        "checker_precision": round(len(hit) / len(flagged), 3) if flagged else None,
        "checker_recall": round(len(hit) / len(bad), 3) if bad else None,
    }


def _num(v) -> str:
    return "n/a" if v is None else str(v)


def render(settings: Settings) -> str:
    rows = compare(settings)
    lines = ["| records | programmes | fields | draft unchanged | edited | dropped | added | checker precision | checker recall |",
             "|---|---|---|---|---|---|---|---|---|"]
    for tier, label in (("human", "human tier (headline)"), (None, "all (second_pass not independent)")):
        s = summarize(rows, tier)
        o = s["outcomes"]
        lines.append(f"| {label} | {s['programmes']} | {s['fields']} | {_num(s['draft_accuracy'])} | {o.get('edited', 0)} | "
                     f"{o.get('dropped', 0)} | {o.get('added', 0)} | {_num(s['checker_precision'])} | {_num(s['checker_recall'])} |")
    return "\n".join(lines)
