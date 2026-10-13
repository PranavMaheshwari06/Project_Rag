"""Local review screen (`make review`, http://127.0.0.1:8001). A separate app
from `api/` so nothing admin-only is ever part of the public service.

Shows each extracted field next to its quote and the full page text. A human
ticks every field, then Save writes data/verified/<slug>.json. Save refuses a
record whose quotes are not found in the pages, so the verified files keep the
same guarantee as the drafts."""

import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError

from core.config import get_settings
from extraction.extract import FIELDS, ProgrammeSource, check_quotes, collect_sources
from extraction.schemas import ProgramRequirements

app = FastAPI(title="Requirements review")

# words that suggest a not_published field is actually on the page (a missed field)
HINTS = {
    "degree_requirement": r"bachelor|undergraduate degree",
    "min_total_ects": r"\d+\s*(ECTS|credits|CP)\b",
    "subject_credits": r"\d+\s*(ECTS|credits|CP)\b",
    "min_grade_german_scale": r"minimum grade|grade point|\bGPA\b|final grade|Durchschnittsnote",
    "english": r"IELTS|TOEFL|CEFR|Cambridge|English (language )?(proficiency|skills|certificate)",
    "entrance_tests": r"\bGRE\b|\bGATE\b|GMAT|aptitude|entrance (exam|test)",
    "german": r"German (language|proficiency|skills)|DSH|TestDaF|Deutsch",
    "work_experience": r"work experience|internship|professional experience",
    "aps_required": r"\bAPS\b|Akademische Pr",
    "application_route": r"uni-assist|application portal|apply online",
    "deadlines": r"deadline|application period|apply (by|until)|\d{1,2}(st|nd|rd|th)? (January|February|March|April|May|June|July|August|September|October|November|December)",
    "selection_process": r"selection|interview|aptitude|motivation letter|essay",
    "required_documents": r"documents|transcript|CV\b|curriculum vitae",
    "tuition_eur_per_semester_non_eu": r"tuition|fees?\b",
    "semester_fee_eur": r"semester (fee|contribution)|student union fee",
    "language_of_instruction": r"taught in|language of instruction|instruction language",
}


@lru_cache
def sources() -> dict[str, ProgrammeSource]:
    return {s.slug: s for s in collect_sources(get_settings())}


def _file(kind: str, slug: str) -> Path:
    s = get_settings()
    return s.resolve(getattr(s.paths, f"{kind}_dir")) / f"{slug}.json"


def _src(slug: str) -> ProgrammeSource:
    if slug not in sources():
        raise HTTPException(404, "unknown programme")
    return sources()[slug]


def _numbers(text: str) -> set[float]:
    text = re.sub(r"(?<=\d)[,\u202f ](?=\d{3}\b)", "", text)  # 6,000 -> 6000
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)}


def flags(rec: ProgramRequirements, docs: dict[str, str]) -> dict[str, list[str]]:
    """Cheap automatic warnings that tell the reviewer where to look; they never change a value."""
    out: dict[str, list[str]] = {}
    dump = rec.model_dump(mode="json")
    for name in FIELDS:
        f = getattr(rec, name)
        msgs = []
        if f.status == "stated":
            missing = _numbers(json.dumps(dump[name]["value"])) - _numbers(f.quote)
            if missing:
                msgs.append(f"value has numbers that are not in the quote: {', '.join(f'{n:g}' for n in sorted(missing))}")
        else:
            for doc_id, text in docs.items():
                if m := re.search(HINTS[name], text, re.I):
                    around = text[max(0, m.start() - 70) : m.end() + 70].replace("\n", " ")
                    msgs.append(f"page mentions '{m.group(0)}' in {doc_id}: ...{around}...")
        if msgs:
            out[name] = msgs
    return out


def checks(slug: str, docs: dict[str, str]) -> dict[str, dict]:
    """The cross-checker's verdict per field. A suggested value goes through
    the same schema and quote-in-page check as a draft; one that fails is
    marked invalid and the screen offers no button for it."""
    path = _file("checked", slug)
    if not path.exists():
        return {}
    out = {}
    for name, c in json.loads(path.read_text(encoding="utf-8"))["fields"].items():
        if name not in FIELDS:
            continue
        c = dict(c)
        if c.get("value") is not None:
            try:
                cited = ProgramRequirements.model_fields[name].annotation.model_validate(
                    {"status": "stated", "value": c["value"], "quote": c.get("quote"), "doc_id": c.get("doc_id")})
                rec = ProgramRequirements(university="", programme="", source_doc_ids=[], **{name: cited})
                bad = check_quotes(rec, docs, get_settings().extraction.min_quote_words)
                c["value"] = cited.model_dump(mode="json")["value"]  # normalised, e.g. test-name aliases
                if bad:
                    c["invalid"] = bad[0]
            except ValidationError as exc:
                c["invalid"] = f"value does not fit the schema: {str(exc)[:300]}"
        out[name] = c
    return out


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("review.html"))


@app.get("/api/programmes")
def list_programmes():
    return [
        {
            "slug": slug,
            "university": s.university,
            "programme": s.programme,
            "status": "verified" if _file("verified", slug).exists() else "draft" if _file("extracted", slug).exists() else "no draft",
        }
        for slug, s in sources().items()
    ]


@app.get("/api/programmes/{slug}")
def get_programme(slug: str):
    src = _src(slug)
    verified = _file("verified", slug)
    path = verified if verified.exists() else _file("extracted", slug)
    if not path.exists():
        raise HTTPException(404, "no draft yet; run make extract")
    data = json.loads(path.read_text(encoding="utf-8"))
    rec = ProgramRequirements.model_validate(data["record"])
    return {
        "slug": slug,
        "verified": verified.exists(),
        "record": rec.model_dump(mode="json"),
        "fields": FIELDS,
        "docs": src.docs,
        "flags": flags(rec, src.docs),
        "checks": checks(slug, src.docs),
        "rejected_quotes": data.get("rejected_quotes", []),
    }


@app.put("/api/programmes/{slug}")
def save_programme(slug: str, body: dict = Body(...)):
    src = _src(slug)
    try:
        rec = ProgramRequirements.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(422, str(exc)[:1500])
    rec.university, rec.programme, rec.source_doc_ids, rec.verified = src.university, src.programme, list(src.docs), True
    bad = check_quotes(rec.model_copy(deep=True), src.docs, get_settings().extraction.min_quote_words)
    if bad:
        raise HTTPException(422, "quote not found in its page, fix or mark not published:\n" + "\n".join(bad))
    draft = _file("extracted", slug)
    out = _file("verified", slug)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draft_model": json.loads(draft.read_text(encoding="utf-8")).get("model") if draft.exists() else None,
        "record": rec.model_dump(mode="json"),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"saved": str(out.name)}
