"""Financial rules: visa proof of funds from a cited mission page, kept apart
from the programme rule files because they belong to the visa route, not to a
programme's verified record. The file carries its fetch and re-check dates;
after the re-check date a report says so."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from eligibility.rules import Rule, record_hash


class FinanceRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["finance-v1"]
    fetched_on: date
    recheck_after: date
    rules: list[Rule]

    @model_validator(mode="after")
    def _finance_only(self):
        if any(r.category != "finance" for r in self.rules):
            raise ValueError("a financial-rule file holds finance rules only")
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("duplicate rule id")
        return self


def load_finance(path: str) -> FinanceRules:
    return FinanceRules.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def finance_hash(finance: FinanceRules) -> str:
    return record_hash(finance.model_dump(mode="json"))
