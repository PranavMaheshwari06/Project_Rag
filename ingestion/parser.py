"""Normalizes raw docs into markdown-ish text the chunker understands:
'#' headings, fenced code blocks, plain paragraphs, markdown table rows.
HTML goes through BeautifulSoup, PDF through pdfplumber; markdown mostly
passes through. No per-site selectors: the only structural rule is "prefer
<main> when the page has one"."""

import io
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from ingestion.crawler import RawDoc

H1_RE = re.compile(r"^#\s+(.*)", re.MULTILINE)


@dataclass
class ParsedDoc:
    doc_id: str
    source: str
    url: str
    title: str
    text: str
    meta: dict = field(default_factory=dict)


def parse(raw: RawDoc, max_pdf_pages: int = 80) -> ParsedDoc:
    if raw.kind == "html":
        text, title = _from_html(raw.content)
    elif raw.kind == "pdf":
        # PDF metadata titles are mostly junk ("Microsoft Word - x.docx"); the registry name wins
        text, title = _from_pdf(raw.content, max_pdf_pages)[0], None
    else:
        text, title = _from_markdown(raw.content)
    return ParsedDoc(
        doc_id=raw.doc_id,
        source=raw.source,
        url=raw.url,
        title=title or raw.title_hint,
        text=text,
        meta=raw.meta,
    )


def _from_markdown(md: str) -> tuple[str, str | None]:
    match = H1_RE.search(md)
    return md, match.group(1).strip() if match else None


def _from_html(html: str) -> tuple[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["nav", "header", "footer", "aside", "script", "style", "form", "noscript"]):
        tag.decompose()

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    body = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup
    lines: list[str] = []
    for el in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "ul", "ol", "table", "dl"]):
        if el.find_parent(["pre", "li", "table", "dl"]):
            continue  # already rendered by the parent element
        if el.name[0] == "h":
            level = min(int(el.name[1]), 4)  # the chunker splits on h1-h4
            heading = el.get_text(" ", strip=True)
            lines.append("#" * level + " " + heading)
            if el.name == "h1" and not title:
                title = heading
        elif el.name == "pre":
            code = el.get_text().rstrip("\n")
            lang = _guess_lang(el)
            lines.append(f"```{lang}\n{code}\n```")
        elif el.name in ("ul", "ol"):
            for li in el.find_all("li", recursive=False):
                lines.append("- " + li.get_text(" ", strip=True))
        elif el.name == "table":
            rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])] for tr in el.find_all("tr")]
            lines.append(_md_table(rows))
        elif el.name == "dl":
            for dt in el.find_all("dt"):
                dd = dt.find_next_sibling("dd")
                lines.append(f"- {dt.get_text(' ', strip=True)}: {dd.get_text(' ', strip=True) if dd else ''}")
        else:
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(text)
    return "\n\n".join(lines), title


def _md_table(rows: list[list[str | None]]) -> str:
    """Requirement pages put the numbers in tables (grade, IELTS, deadline);
    one row per line keeps label and value together in the same chunk."""
    rows = [[(c or "").replace("|", "/").replace("\n", " ").strip() for c in r] for r in rows if any(r)]
    if not rows:
        return ""
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * len(rows[0])]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def _from_pdf(data: bytes, max_pages: int) -> tuple[str, str | None]:
    import pdfplumber  # only needed for PDFs; keeps import cost off the HTML path

    parts: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages[:max_pages]:
            tables = page.find_tables()
            rest = page
            for t in tables:
                rest = rest.outside_bbox(t.bbox)  # table text appears once, as a table
            parts.append(rest.extract_text() or "")
            parts.extend(_md_table(t.extract()) for t in tables)
    # ponytail: tables go after their page's text, not in reading position; fine for retrieval
    return "\n\n".join(p for p in parts if p.strip()), None


def _guess_lang(pre_tag) -> str:
    code = pre_tag.find("code")
    classes = (code.get("class") if code else None) or pre_tag.get("class") or []
    for cls in classes:
        if cls.startswith("language-"):
            return cls.removeprefix("language-")
    return ""
