"""`check_eligibility.py --validate`: a quote that is not in the verified record
can only be checked against the cached page. Without the cache it is reported
as not checked; with --check-cache a missing page is an error, so a local run
cannot pass silently."""

import importlib.util
from pathlib import Path

from core.config import load_settings

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_eligibility.py"
spec = importlib.util.spec_from_file_location("check_eligibility_script", SCRIPT)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def settings_without_cache(tmp_path):
    settings = load_settings()
    settings.paths.raw_dir = str(tmp_path)  # empty: no cached page exists
    return settings


def test_missing_cache_is_only_a_note_by_default(tmp_path, capsys):
    assert cli.validate(settings_without_cache(tmp_path)) == []
    assert "cached page unavailable, not checked" in capsys.readouterr().out


def test_missing_cache_is_an_error_with_check_cache(tmp_path):
    errors = cli.validate(settings_without_cache(tmp_path), check_cache=True)
    assert errors and all("cached page unavailable" in e for e in errors)
    assert any(e.startswith("tum-m-sc-informatics: english:") for e in errors)
