"""Crawler politeness and caching against a fake site (httpx.MockTransport, no network)."""

import hashlib
import json

import httpx

from core.config import Settings
from ingestion.crawler import crawl
from ingestion.registry import RegistryEntry

ROBOTS = "User-agent: *\nDisallow: /private/\n"
PAGE = b"<html><body><main><h1>Admission</h1><p>IELTS 6.5</p></main></body></html>"


def _settings(tmp_path):
    s = Settings()
    s.paths.raw_dir = str(tmp_path / "raw")
    s.paths.manifest_path = str(tmp_path / "manifest.json")
    s.crawl.delay_seconds = 0
    return s


def _client(hits):
    def handler(request):
        hits.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS)
        if request.url.path == "/broken":
            return httpx.Response(503)
        return httpx.Response(200, content=PAGE, headers={"content-type": "text/html; charset=utf-8"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def _entry(id_, path):
    return RegistryEntry(id=id_, url=f"https://uni.example{path}", country="DE", layer="university")


def test_robots_respected_and_page_cached(tmp_path):
    settings, hits = _settings(tmp_path), []
    entries = [_entry("ok", "/msc"), _entry("secret", "/private/x"), _entry("down", "/broken")]
    report = crawl(entries, settings, client=_client(hits))

    assert [r["result"] for r in report] == ["ok", "robots-disallowed", "error"]
    assert "/private/x" not in hits  # never requested
    assert (tmp_path / "raw" / "ok.html").read_bytes() == PAGE
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["ok"]["sha256"] == hashlib.sha256(PAGE).hexdigest()
    assert manifest["ok"]["content_type"] == "text/html"
    assert "robots" in manifest["secret"]["error"]
    assert manifest["down"]["error"] and "file" not in manifest["down"]

    # second run: cached page is not fetched again
    hits.clear()
    report = crawl(entries[:1], settings, client=_client(hits))
    assert report[0]["result"] == "cached" and hits == []

    # a registry URL edit under the same id is fetched again, not served from cache
    report = crawl([_entry("ok", "/msc-new")], settings, client=_client(hits))
    assert report[0]["result"] == "ok" and "/msc-new" in hits


def test_failed_refresh_keeps_previous_copy(tmp_path):
    settings, hits = _settings(tmp_path), []
    crawl([_entry("p", "/msc")], settings, client=_client(hits))
    moved = _entry("p", "/broken")  # same id, the site now fails
    crawl([moved], settings, refresh=True, client=_client(hits))

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["p"]["error"] and manifest["p"]["file"] == "p.html"
    assert (tmp_path / "raw" / "p.html").read_bytes() == PAGE
