"""Source registry: the hand-edited list of every URL the corpus is built from.
Validated on load so a typo in a layer or stage fails loudly instead of quietly
producing chunks nobody can filter on."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, HttpUrl

Layer = Literal["rules", "scholarship", "university"]
Stage = Literal["before_applying", "visa_document", "visa_funds", "arrival", "after_graduation"]


class RegistryEntry(BaseModel):
    id: str
    url: HttpUrl
    country: str
    layer: Layer
    stage: Stage | None = None
    university: str | None = None
    programme: str | None = None
    title: str | None = None


def load_registry(path: Path) -> list[RegistryEntry]:
    entries = [RegistryEntry.model_validate(e) for e in yaml.safe_load(path.read_text(encoding="utf-8")) or []]
    seen: set[str] = set()
    for e in entries:
        if e.id in seen:
            raise ValueError(f"duplicate registry id: {e.id}")
        seen.add(e.id)
    return entries
