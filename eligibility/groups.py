"""Named country groups (EHEA, Lisbon Convention, EU) loaded from a cited file.

A country is a `member`, `uncertain` (listed but the group's note says a
university may not count it) or not a member. Names are matched case-insensitive
after alias mapping (Czechia = Czech Republic). Not on the list means not a
member: for an exemption the student is told the test is needed."""

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CountryGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    source_url: str
    fetched_on: date
    recheck_after: date
    reviewed_by: Literal["pending", "model", "human"]
    members: list[str]
    uncertain: list[str] = []  # also in `members`, but membership is disputed
    uncertain_note: str | None = None


class CountryGroups(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    groups: dict[str, CountryGroup]
    aliases: dict[str, str] = {}

    def canonical(self, country: str) -> str:
        key = country.strip().casefold()
        return self.aliases.get(key, country.strip())

    def membership(self, group: str, country: str) -> Literal["member", "uncertain", "no"]:
        g = self.groups[group]
        name = self.canonical(country).casefold()
        if name in {u.casefold() for u in g.uncertain}:
            return "uncertain"
        return "member" if name in {m.casefold() for m in g.members} else "no"


@lru_cache
def load_groups(path: str) -> CountryGroups:
    return CountryGroups.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
