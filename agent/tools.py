"""The agent's read-only tools. Each returns a ToolResult: a short text the model
reads, the evidence it may cite, and a typed payload for the trace. Facts come
from retrieval, the verified records and the deterministic engine; the model only
chooses which tool to call and explains what comes back. check_eligibility gets
its profile from the caller, never from the model, and the model sees verdicts,
not the student's own numbers."""

import json
from datetime import date
from decimal import Decimal
from functools import cached_property
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from core.config import Settings
from eligibility.engine import check_eligibility
from eligibility.finance import load_finance
from eligibility.grade import convert_grade
from eligibility.profile import Profile
from eligibility.rules import load_ruleset, record_tier
from ingestion.registry import load_registry
from schemas.common import Chunk

TIER_NOTE = {
    "human": "every field was checked by hand against the cited page",
    "second_pass": "re-read against the cited pages, not hand-checked field by field",
}


class ToolResult(BaseModel):
    ok: bool
    text: str  # what the model reads, without the evidence passages
    evidence: list[Chunk] = []  # citable sources; the loop numbers them
    data: dict = {}  # typed payload for the step trace


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchArgs(_Args):
    query: str = Field(min_length=1, max_length=300)


class ProgrammeArgs(_Args):
    programme: str = Field(min_length=1)


class RequirementArgs(ProgrammeArgs):
    fields: list[str] | None = None  # None = every field


class GradeArgs(_Args):
    best: Decimal
    passing: Decimal
    obtained: Decimal


TOOLS: dict[str, tuple[type[_Args], str]] = {
    "search_sources": (SearchArgs, "Search the official pages (hybrid retrieval + rerank). "
                       'Args: {"query": str}. Use for visa, funds, city, scholarship and other questions.'),
    "get_requirements": (RequirementArgs, "Verified admission facts of one programme, each with its source quote. "
                         'Args: {"programme": slug, "fields": [field names] or null}.'),
    "check_eligibility": (ProgrammeArgs, "Run the deterministic eligibility engine on the user's own profile for "
                          'one programme. Args: {"programme": slug}. Only works when the user supplied a profile.'),
    "convert_grade": (GradeArgs, "Estimate a German grade with the modified Bavarian formula (not official). "
                      'Args: {"best": number, "passing": number, "obtained": number}.'),
}


class Toolbox:
    def __init__(self, settings: Settings, pipeline, profile: Profile | None = None, as_of: date | None = None,
                 intake: Literal["winter", "summer"] | None = None, starting_year: int | None = None):
        self.settings, self.pipeline, self.profile = settings, pipeline, profile
        self.as_of, self.intake, self.starting_year = as_of, intake, starting_year

    @cached_property
    def programmes(self) -> list[str]:
        """Slugs with both a verified record and a rule file; never a path from the model."""
        rules = {p.stem for p in Path(self.settings.paths.rules_dir).glob("*.json")}
        return sorted(p.stem for p in Path(self.settings.paths.verified_dir).glob("*.json") if p.stem in rules)

    @cached_property
    def _sources(self) -> dict[str, tuple[str, str]]:
        entries = load_registry(Path(self.settings.paths.registry_path))
        return {e.id: (str(e.url), e.title or e.id) for e in entries}

    def call(self, name: str, args: dict) -> ToolResult:
        if name not in TOOLS:
            return ToolResult(ok=False, text=f"unknown tool {name!r}; tools: {', '.join(TOOLS)}")
        model, _ = TOOLS[name]
        try:
            parsed = model.model_validate(args)
        except ValidationError as e:
            return ToolResult(ok=False, text=f"bad arguments for {name}: {e.errors(include_url=False)}")
        if isinstance(parsed, ProgrammeArgs) and parsed.programme not in self.programmes:
            return ToolResult(ok=False, text=f"{parsed.programme!r} is not covered; covered: {', '.join(self.programmes)}")
        try:
            return getattr(self, name)(parsed)
        except Exception as e:  # a failing tool is a tool error, not a crash; the message stays out
            return ToolResult(ok=False, text=f"{name} failed ({type(e).__name__}).")

    def search_sources(self, a: SearchArgs) -> ToolResult:
        hits = self.pipeline.search(a.query, mode="hybrid_rerank", top_k=self.settings.agent.search_top_k)
        # the one-shot refusal gate, per search: a weak best hit means the corpus does not cover it
        if not hits or (hits[0].rerank_score or 0.0) < self.settings.generation.refusal_threshold:
            return ToolResult(ok=True, text="No passage is relevant enough to cite.", data={"hits": 0})
        return ToolResult(ok=True, text=f"{len(hits)} passages found.", evidence=[h.chunk for h in hits],
                          data={"hits": len(hits), "doc_ids": [h.chunk.doc_id for h in hits]})

    def _record(self, slug: str) -> dict:
        path = Path(self.settings.paths.verified_dir) / f"{slug}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _evidence(self, chunk_id: str, doc_id: str, title: str, section: str, text: str) -> Chunk:
        url, page = self._sources.get(doc_id, ("", doc_id))
        return Chunk(chunk_id=chunk_id, doc_id=doc_id, source=doc_id, title=f"{title} ({page})",
                     section_path=section, url=url, text=text, token_count=0)

    def get_requirements(self, a: RequirementArgs) -> ToolResult:
        wrapper = self._record(a.programme)
        record, tier = wrapper["record"], wrapper["tier"]
        cited = {k: v for k, v in record.items() if isinstance(v, dict) and "status" in v}
        names = a.fields if a.fields is not None else list(cited)
        unknown = [n for n in names if n not in cited]
        if unknown:
            return ToolResult(ok=False, text=f"unknown fields {unknown}; fields: {', '.join(cited)}")
        title = f"{record['university']} {record['programme']}"
        lines, evidence = [f"{title}, verified record (tier {tier}: {TIER_NOTE[tier]})."], []
        for n in names:
            f = cited[n]
            if f["status"] != "stated":
                lines.append(f"- {n}: not published on the programme's pages.")
                continue
            value = json.dumps(f["value"], ensure_ascii=False)
            evidence.append(self._evidence(f"record:{a.programme}#{n}", f["doc_id"], title, n,
                                           f'{n}: {value}. Source quote: "{f["quote"]}"'))
        return ToolResult(ok=True, text="\n".join(lines), evidence=evidence,
                          data={"programme": a.programme, "tier": tier, "fields": names})

    def check_eligibility(self, a: ProgrammeArgs) -> ToolResult:
        if self.profile is None:
            return ToolResult(ok=False, text="The user supplied no profile. Do not guess one; say what is missing.")
        rules, stale = load_ruleset(self.settings, a.programme)
        report = check_eligibility(self.profile, rules, stale, as_of=self.as_of,
                                   tier=record_tier(self.settings, a.programme), intake=self.intake,
                                   starting_year=self.starting_year,
                                   finance=load_finance(self.settings.paths.finance_rules_path))
        lines = [f"Engine headline (report it as is, do not change it): {report.headline}"]
        if stale:
            lines.append("The programme rules are out of date against the verified record, so only the visa "
                         "funds rules were checked; the programme's own requirements need a re-check.")
        evidence = []
        for c in report.criteria:  # verdicts and requirements only: the student's values stay out
            line = f"- {c.label}: {c.verdict}" + (f", required {c.required.rstrip('.')}" if c.required else "")
            lines.append(line + (f". {c.action}" if c.action else ""))
            evidence += [self._evidence(f"rule:{a.programme}#{c.rule_id}:{i}", cit.doc_id, c.label, c.rule_id,
                                        f'{c.label}: "{cit.quote}"') for i, cit in enumerate(c.citations)]
        lines += report.notices
        return ToolResult(ok=True, text="\n".join(lines), evidence=evidence,
                          data={"programme": a.programme, "headline": report.headline, "stale": stale,
                                "verdicts": {c.rule_id: c.verdict for c in report.criteria}})

    def convert_grade(self, a: GradeArgs) -> ToolResult:
        try:
            g = convert_grade(a.best, a.passing, a.obtained)
        except ValueError as e:
            return ToolResult(ok=False, text=str(e))
        except ArithmeticError:  # e.g. 9e999999 overflows the Decimal context
            return ToolResult(ok=False, text="grade values out of range")
        return ToolResult(ok=True, text=f"Estimated German grade {g.german:.2f} ({g.formula}); an estimate, "
                          "not an official conversion.", data={"german": str(g.german)})
