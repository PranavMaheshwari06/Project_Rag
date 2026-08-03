"""Normalizes raw docs into markdown-ish text the chunker understands:
'#' headings, fenced code blocks, plain paragraphs. HTML goes through
BeautifulSoup; markdown mostly passes through."""

import re
from dataclasses import dataclass

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


def parse(raw: RawDoc) -> ParsedDoc:
    if raw.kind == "html":
        text, title = _from_html(raw.content)
    else:
        text, title = _from_markdown(raw.content)
    return ParsedDoc(
        doc_id=raw.doc_id,
        source=raw.source,
        url=raw.url,
        title=title or raw.title_hint,
        text=text,
    )


def _from_markdown(md: str) -> tuple[str, str | None]:
    match = H1_RE.search(md)
    return md, match.group(1).strip() if match else None


def _from_html(html: str) -> tuple[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["nav", "header", "footer", "aside", "script", "style"]):
        tag.decompose()

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    body = soup.body or soup
    lines: list[str] = []
    for el in body.find_all(["h1", "h2", "h3", "h4", "p", "pre", "ul", "ol"]):
        if el.find_parent(["pre", "li"]):
            continue  # already rendered by the parent element
        if el.name in ("h1", "h2", "h3", "h4"):
            level = int(el.name[1])
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
        else:
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(text)
    return "\n\n".join(lines), title


def _guess_lang(pre_tag) -> str:
    code = pre_tag.find("code")
    classes = (code.get("class") if code else None) or pre_tag.get("class") or []
    for cls in classes:
        if cls.startswith("language-"):
            return cls.removeprefix("language-")
    return ""
