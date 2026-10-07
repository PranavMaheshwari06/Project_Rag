"""Registry validation: the real file loads, and typos fail loudly. No network."""

import pytest
from pydantic import ValidationError

from core.config import get_settings
from ingestion.registry import load_registry


def test_real_registry_loads():
    settings = get_settings()
    load_registry(settings.resolve(settings.paths.registry_path))  # raises on bad enum / duplicate id


def test_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "r.yaml"
    path.write_text("- {id: a, url: 'https://x.org', country: DE, layer: rules}\n" * 2)
    with pytest.raises(ValueError, match="duplicate"):
        load_registry(path)


def test_rejects_unknown_layer(tmp_path):
    path = tmp_path / "r.yaml"
    path.write_text("- {id: a, url: 'https://x.org', country: DE, layer: rumours}\n")
    with pytest.raises(ValidationError):
        load_registry(path)
