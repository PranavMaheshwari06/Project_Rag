from ingestion.cleaner import clean


def test_fenced_code_kept_byte_for_byte():
    code = "```html\n<!-- keep me -->\n<p>a</p>\n\n\n\n<p>b</p>\n```"
    out = clean(f"intro <!-- drop me -->\n\n\n\n{code}\n\noutro")
    assert code in out
    assert "drop me" not in out
    assert out.startswith("intro\n\n```")  # blank run in prose collapsed to one


def test_soft_hyphen_and_nbsp_normalised():
    assert clean("Sperr­konto amount") == "Sperrkonto amount\n"
