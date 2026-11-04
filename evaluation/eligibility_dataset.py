"""Eligibility evaluation cases: a profile, a target, and labels written from
the cited sources before the engine is run on them (plan section 7).

A case authored by a person (`author: human`) must carry `frozen_on`, the date
its labels were committed; the commit is the proof they predate engine output.
Every expected criterion carries its own citation."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from core.config import Settings
from eligibility.profile import Profile
from eligibility.report import Headline
from eligibility.rules import Citation, Verdict, load_ruleset

DATASET_SCHEMA_VERSION = "eligibility-cases-v1"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExpectedCriterion(Strict):
    rule_id: str
    verdict: Verdict
    citations: list[Citation] = Field(min_length=1)


class EligibilityCase(Strict):
    schema_version: Literal["eligibility-cases-v1"] = DATASET_SCHEMA_VERSION
    case_id: str = Field(min_length=1)
    profile: Profile
    slug: str
    intake: Literal["winter", "summer"]
    starting_year: int
    as_of: date
    expected_headline: Headline
    expected_criteria: list[ExpectedCriterion] = []
    rationale: str = Field(min_length=1)
    citations: list[Citation] = Field(min_length=1)
    author: Literal["human", "assisted"]
    reviewer: Literal["human", "model"] | None = None
    related_to: str | None = None  # case id of the base case this one varies
    frozen_on: date | None = None

    @model_validator(mode="after")
    def _human_labels_are_frozen(self):
        if self.author == "human" and self.frozen_on is None:
            raise ValueError("a case authored by a human needs frozen_on (the date its labels were committed)")
        return self


def load_cases(path: Path) -> list[EligibilityCase]:
    """JSON Lines, blank lines skipped; a bad line raises with its line number."""
    cases = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(EligibilityCase.model_validate(json.loads(line)))
        except (ValidationError, json.JSONDecodeError) as e:
            raise ValueError(f"{path}: line {n}: {e}") from e
    return cases


def validate_cases(cases: list[EligibilityCase], settings: Settings) -> list[str]:
    """Dataset-level problems the per-case schema cannot see."""
    problems, seen = [], set()
    ids = {c.case_id for c in cases}
    rules_dir = Path(settings.paths.rules_dir)
    for c in cases:
        if c.case_id in seen:
            problems.append(f"{c.case_id}: duplicate case_id")
        seen.add(c.case_id)
        if c.related_to is not None and c.related_to not in ids:
            problems.append(f"{c.case_id}: related_to {c.related_to} is not a case in this dataset")
        if not (rules_dir / f"{c.slug}.json").is_file():
            problems.append(f"{c.case_id}: no rule file for {c.slug}")
            continue
        rule_ids = {r.id for r in load_ruleset(settings, c.slug)[0].rules}
        for e in c.expected_criteria:
            if e.rule_id not in rule_ids:
                problems.append(f"{c.case_id}: rule {e.rule_id} is not in {c.slug}")
    return problems
