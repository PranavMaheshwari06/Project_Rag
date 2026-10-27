"""HTML parsing: main content preferred, tables and definition lists kept
as label/value text. PDF parsing is checked through the real ingest report."""

from ingestion.crawler import RawDoc
from ingestion.parser import parse

HTML = """<html><head><title>MSc Informatics</title></head><body>
<div class="menu"><p>Menu noise</p></div>
<main>
  <h1>MSc Informatics</h1>
  <p>Admission requirements:</p>
  <table><tr><th>Requirement</th><th>Minimum</th></tr>
         <tr><td>IELTS</td><td>6.5</td></tr></table>
  <dl><dt>Deadline</dt><dd>31 May</dd></dl>
  <form><p>Newsletter</p></form>
</main></body></html>"""


def _parse(html):
    return parse(RawDoc(source="s", doc_id="d", title_hint="t", url="https://x", kind="html", content=html))


def test_main_preferred_and_tables_kept():
    doc = _parse(HTML)
    assert doc.title == "MSc Informatics"
    assert "Menu noise" not in doc.text and "Newsletter" not in doc.text
    assert "| Requirement | Minimum |" in doc.text
    assert "| IELTS | 6.5 |" in doc.text
    assert "- Deadline: 31 May" in doc.text


def test_body_fallback_without_main():
    doc = _parse("<html><body><h2>Visa</h2><p>Blocked account required.</p></body></html>")
    assert "## Visa" in doc.text and "Blocked account required." in doc.text


def test_accordion_scope_headings_precede_their_content():
    doc = _parse('''<main><h2>Deadlines</h2>
      <div><a class="accordion-title">German degree</a><dl><dt>Deadline</dt><dd>15 July</dd></dl></div>
      <div><a class="accordion-title">Foreign degree</a><p>31 May</p></div>
      <details><summary>Exemptions</summary><p>Only with proof</p></details>
      <div role="button" aria-expanded="false" aria-controls="profile">Profile tab</div><p>Profile contents</p></main>''')
    assert doc.text.index("#### German degree") < doc.text.index("15 July")
    assert doc.text.index("#### Foreign degree") < doc.text.index("31 May")
    assert doc.text.count("#### Exemptions") == 1
    assert "#### Profile tab" not in doc.text
