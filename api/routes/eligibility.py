"""Eligibility endpoints. /eligibility/check needs no LLM and no key: it runs the
deterministic engine on a confirmed profile. /profile/parse turns pasted text
into an unconfirmed draft. Neither logs nor stores profile text or fields."""

from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_llm_client
from core.config import get_settings
from eligibility.engine import check_eligibility
from eligibility.finance import load_finance
from eligibility.parse import ParsedProfile, ParseError, parse_profile
from eligibility.profile import Profile
from eligibility.report import Report
from eligibility.rules import load_ruleset, record_tier

router = APIRouter()


class CheckRequest(BaseModel):
    profile: Profile
    country: str
    intake: Literal["winter", "summer"]
    starting_year: int
    as_of: date
    targets: list[str] = Field(min_length=1)


class TargetResult(BaseModel):
    slug: str
    status: Literal["checked", "not_covered", "rules_stale"]
    headline: str
    report: Report | None = None


class CheckResponse(BaseModel):
    request_id: str
    results: list[TargetResult]
    notices: list[str] = []


class ParseRequest(BaseModel):
    text: str = Field(min_length=1)


@router.post("/eligibility/check")
def check(body: CheckRequest, request: Request) -> CheckResponse:
    settings = get_settings()
    request_id = getattr(request.state, "request_id", "-")
    if body.country.strip().casefold() != "germany":
        return CheckResponse(request_id=request_id, results=[], notices=[
            "This tool covers Germany only. For other countries, use that country's official study portal."])
    targets = list(dict.fromkeys(body.targets))
    if len(targets) > settings.eligibility.max_targets:
        raise HTTPException(400, f"at most {settings.eligibility.max_targets} programmes per request")
    finance = load_finance(settings.paths.finance_rules_path)
    results = []
    for slug in targets:
        if not (Path(settings.paths.rules_dir) / f"{slug}.json").is_file():
            results.append(TargetResult(slug=slug, status="not_covered", headline="not_covered"))
            continue
        rules, stale = load_ruleset(settings, slug)
        report = check_eligibility(body.profile, rules, stale, as_of=body.as_of, tier=record_tier(settings, slug),
                                   intake=body.intake, starting_year=body.starting_year, finance=finance)
        results.append(TargetResult(slug=slug, status="rules_stale" if stale else "checked",
                                    headline=report.headline, report=report))
    return CheckResponse(request_id=request_id, results=results)


@router.post("/profile/parse")
def parse(body: ParseRequest, llm=Depends(get_llm_client)) -> ParsedProfile:
    limit = get_settings().eligibility.parse_max_chars
    if len(body.text) > limit:
        raise HTTPException(422, f"the text is longer than {limit} characters")
    if not llm.available:
        raise HTTPException(503, "profile parsing needs an LLM key on the server; enter the profile manually")
    try:
        return parse_profile(body.text, llm)
    except ParseError:
        raise HTTPException(502, "the model did not return a usable draft; enter the profile manually")
    except Exception:  # provider errors may echo the prompt: answer without any of it
        raise HTTPException(502, "the profile parser is unavailable right now; enter the profile manually")
