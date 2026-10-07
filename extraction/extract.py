"""LLM extraction: one call per programme over the full cleaned text of its
pages, validated against ProgramRequirements. The LLM only fills fields; a
stated field survives only if its quote appears in the page it cites, so a
value the model invented is dropped back to not_published."""

import json
import logging
import re
from dataclasses import dataclass

from pydantic import ValidationError

from core.config import Settings
from extraction.schemas import ProgramRequirements
from generation.llm_client import LLMClient
from ingestion.cleaner import clean
from ingestion.crawler import load_corpus
from ingestion.parser import parse

log = logging.getLogger(__name__)

META_FIELDS = {"university", "programme", "source_doc_ids", "verified"}
FIELDS = [name for name in ProgramRequirements.model_fields if name not in META_FIELDS]

SYSTEM_PROMPT = """You extract master's admission requirements for ONE programme from official university pages.

Return a JSON object with exactly these keys: {fields}.
Each key maps to an object {{"status", "value", "quote", "doc_id"}}:
- "stated": the pages state it. "value" follows the JSON schema below. "quote" is copied character for character from one document: the whole sentence, bullet or table row that supports the value, never just the number or a single cell. "doc_id" is the id of that document.
- "not_published": the pages do not state it. "value", "quote" and "doc_id" are null.

Rules:
- Use only the documents. Never use outside knowledge, never guess, never round or convert numbers.
- Some pages cover several programmes: only take what applies to "{programme}" at {university}.
- min_grade_german_scale: only if a minimum grade on the German scale (1.0 best, 4.0 pass) is stated.
- english: one entry per accepted test with its minimum score as written.
- entrance_tests: GRE, GATE, GMAT, the university's own aptitude test, etc. Use "one_of" for tests that are alternatives to each other. applies_to_degree_countries lists the countries named (empty if it applies to all applicants).
- german: "none" if the pages say no German is needed.
- work_experience: "counts_in_selection" if internships or work experience earn points or are considered but are not required.
- tuition_eur_per_semester_non_eu: 0 if the pages say there are no tuition fees.

JSON schema for the values:
{schema}"""


@dataclass
class ProgrammeSource:
    university: str
    programme: str
    docs: dict[str, str]  # doc_id -> cleaned text

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", f"{self.university} {self.programme}".lower()).strip("-")


def collect_sources(settings: Settings) -> list[ProgrammeSource]:
    """Each programme gets its own pages plus its university's pages that
    aren't tied to a programme (e.g. a general admission-requirements page)."""
    texts: dict[str, tuple[dict, str]] = {}
    for raw in load_corpus(settings):
        if raw.meta.get("layer") == "university":
            texts[raw.doc_id] = (raw.meta, clean(parse(raw, settings.crawl.max_pdf_pages).text))
    programmes = sorted({(m["university"], m["programme"]) for m, _ in texts.values() if m.get("programme")})
    return [
        ProgrammeSource(uni, prog, {
            doc_id: text
            for doc_id, (meta, text) in texts.items()
            if meta["university"] == uni and meta.get("programme") in (prog, None)
        })
        for uni, prog in programmes
    ]


def build_messages(src: ProgrammeSource) -> list[dict]:
    system = SYSTEM_PROMPT.format(
        fields=", ".join(FIELDS),
        programme=src.programme,
        university=src.university,
        schema=json.dumps(ProgramRequirements.model_json_schema()),
    )
    docs = "\n\n".join(f'<document id="{doc_id}">\n{text}\n</document>' for doc_id, text in src.docs.items())
    return [{"role": "system", "content": system}, {"role": "user", "content": docs}]


def _words(text: str) -> str:
    # quotes are compared on words only: the model may drop markdown, bullets or line breaks
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def check_quotes(rec: ProgramRequirements, docs: dict[str, str], min_words: int) -> list[str]:
    """Reset every stated field whose quote is too short or not in its cited
    doc, and say why. Mutates rec."""
    rejected = []
    for name in FIELDS:
        field = getattr(rec, name)
        if field.status != "stated":
            continue
        quote = _words(field.quote)
        if field.doc_id not in docs:
            reason = f"cites unknown doc {field.doc_id}"
        elif len(quote.split()) < min_words:
            reason = "quote too short to verify"
        elif quote not in _words(docs[field.doc_id]):
            reason = f"quote not found in {field.doc_id}"
        else:
            continue
        rejected.append(f"{name}: {reason}: {field.quote!r}")
        setattr(rec, name, type(field)())
    return rejected


def extract_programme(src: ProgrammeSource, llm: LLMClient, settings: Settings) -> tuple[ProgramRequirements, list[str]]:
    messages = build_messages(src)
    for attempt in range(2):
        reply = llm.complete(messages, json_mode=True)
        try:
            data = json.loads(reply)
            data.update(university=src.university, programme=src.programme,
                        source_doc_ids=list(src.docs), verified=False)
            rec = ProgramRequirements.model_validate(data)
            break
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt:
                raise
            log.warning("invalid extraction for %s, retrying once: %s", src.slug, str(exc)[:300])
            messages = messages + [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": f"That JSON was invalid:\n{str(exc)[:2000]}\nReturn the corrected JSON object only."},
            ]
    return rec, check_quotes(rec, src.docs, settings.extraction.min_quote_words)
