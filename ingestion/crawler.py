"""Polite crawler plus the offline corpus loader.

`crawl` is the only network step: registry URL -> robots.txt check -> per-host
delay -> raw file in data/raw/ + a manifest record (crawl date, sha256, error).
A failed fetch keeps the previous raw file, so a flaky site never loses data.

`load_corpus` is offline: it joins registry + manifest + raw cache into
RawDocs. Entries that were never fetched are skipped with a log line."""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from ingestion.registry import RegistryEntry, load_registry

log = logging.getLogger(__name__)


@dataclass
class RawDoc:
    source: str
    doc_id: str
    title_hint: str
    url: str
    kind: str  # "html" | "markdown" | "pdf"
    content: str | bytes
    meta: dict = field(default_factory=dict)  # provenance carried onto every chunk


def kind_for(content_type: str) -> str:
    if "pdf" in content_type:
        return "pdf"
    if "html" in content_type:
        return "html"
    return "markdown"


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _robots(client: httpx.Client, origin: str) -> tuple[RobotFileParser, str]:
    """Returns the parsed rules and a note on how they were obtained, so a
    refusal in the report says whether the site said no or was unreachable."""
    rp = RobotFileParser()
    try:
        resp = client.get(f"{origin}/robots.txt")
    except httpx.HTTPError as exc:
        rp.disallow_all = True  # can't read the rules -> don't guess
        return rp, f"robots.txt unreachable ({type(exc).__name__})"
    if resp.status_code in (401, 403) or resp.status_code >= 500:
        rp.disallow_all = True
        return rp, f"robots.txt returned {resp.status_code}"
    if resp.status_code >= 400:
        rp.allow_all = True  # no robots.txt means no restrictions
    else:
        rp.parse(resp.text.splitlines())
    return rp, "disallowed by robots.txt rules"


def _fetch(client: httpx.Client, url: str, max_bytes: int) -> tuple[httpx.Response, bytes]:
    """Streams so an oversized file is cut off without being held in memory."""
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        body = bytearray()
        for part in resp.iter_bytes():
            body.extend(part)
            if len(body) > max_bytes:
                raise ValueError(f"response larger than {max_bytes} bytes")
    return resp, bytes(body)


def crawl(entries: list[RegistryEntry], settings, refresh: bool = False, client: httpx.Client | None = None) -> list[dict]:
    """Fetches every entry not already cached (all of them with refresh=True),
    updates the manifest and returns one report row per entry."""
    cfg = settings.crawl
    raw_dir = settings.resolve(settings.paths.raw_dir)
    manifest_path = settings.resolve(settings.paths.manifest_path)
    manifest = load_manifest(manifest_path)
    client = client or httpx.Client(
        headers={"User-Agent": cfg.user_agent}, follow_redirects=True, timeout=cfg.timeout_seconds
    )
    robots: dict[str, tuple[RobotFileParser, str]] = {}
    last_hit: dict[str, float] = {}
    report: list[dict] = []

    for entry in entries:
        url = str(entry.url)
        prev = manifest.get(entry.id, {})
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cached = prev.get("file") and (raw_dir / prev["file"]).exists() and prev.get("url") == url
        if cached and not refresh:
            report.append({"id": entry.id, "result": "cached"})
            continue

        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in robots:
            robots[origin] = _robots(client, origin)
        rp, robots_note = robots[origin]
        if not rp.can_fetch(cfg.user_agent, url):
            manifest[entry.id] = {**prev, "url": url, "checked_at": now, "error": robots_note}
            report.append({"id": entry.id, "result": "robots-disallowed", "detail": robots_note})
            continue

        delay = max(cfg.delay_seconds, rp.crawl_delay(cfg.user_agent) or 0)
        wait = last_hit.get(origin, 0) + delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        try:
            resp, body = _fetch(client, url, cfg.max_bytes)
        except (httpx.HTTPError, ValueError) as exc:
            manifest[entry.id] = {**prev, "url": url, "checked_at": now, "error": str(exc)[:300]}
            report.append({"id": entry.id, "result": "error", "detail": str(exc)[:120]})
            continue
        finally:
            last_hit[origin] = time.monotonic()

        content_type = resp.headers.get("content-type", "").split(";")[0].strip()
        file = entry.id + {"pdf": ".pdf", "html": ".html", "markdown": ".md"}[kind_for(content_type)]
        (raw_dir / file).parent.mkdir(parents=True, exist_ok=True)
        (raw_dir / file).write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()
        manifest[entry.id] = {
            "url": url,
            "final_url": str(resp.url),
            "status": resp.status_code,
            "content_type": content_type,
            "fetched_at": now,
            "checked_at": now,
            "sha256": sha,
            "changed": prev.get("sha256") not in (None, sha),
            "file": file,
            "error": None,
        }
        row = {"id": entry.id, "result": "ok", "type": content_type, "bytes": len(body)}
        if str(resp.url).rstrip("/") != url.rstrip("/"):
            row["redirected_to"] = str(resp.url)  # a homepage here means the page moved
        report.append(row)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def load_corpus(settings) -> list[RawDoc]:
    entries = load_registry(settings.resolve(settings.paths.registry_path))
    manifest = load_manifest(settings.resolve(settings.paths.manifest_path))
    raw_dir = settings.resolve(settings.paths.raw_dir)

    docs: list[RawDoc] = []
    for entry in entries:
        rec = manifest.get(entry.id)
        path = raw_dir / rec["file"] if rec and rec.get("file") else None
        if not path or not path.exists():
            log.warning("skipping %s: not crawled (run `make crawl`)", entry.id)
            continue
        kind = kind_for(rec["content_type"])
        docs.append(
            RawDoc(
                source=entry.university or entry.layer,
                doc_id=entry.id,
                title_hint=entry.title or entry.id.rsplit("/", 1)[-1].replace("-", " ").title(),
                url=rec.get("final_url") or str(entry.url),
                kind=kind,
                content=path.read_bytes() if kind == "pdf" else path.read_text(encoding="utf-8"),
                meta={
                    "country": entry.country,
                    "layer": entry.layer,
                    "stage": entry.stage,
                    "university": entry.university,
                    "programme": entry.programme,
                    "crawled_at": rec.get("fetched_at"),
                },
            )
        )
    return docs
