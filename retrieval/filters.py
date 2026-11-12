"""Metadata filters for retrieval, and a rule-based detector that reads them
from the question (no LLM).

A filter maps a chunk field to the values allowed. `university` and `programme`
are scopes: a chunk with no value there (a country rule, or a university-wide
page) applies to every scope and is kept. `stage` and `layer` match exactly."""

import re
from typing import get_args

from ingestion.registry import Layer, Stage
from schemas.common import Chunk

SCOPES = {"university", "programme"}

# university -> name patterns; programme -> name patterns, per university.
# tests/test_retrieval_filters.py checks this table covers sources/registry.yaml.
UNIVERSITIES = {
    "TUM": r"\btum\b|technical university of munich|\btu munich\b|munich|münchen",
    "RWTH Aachen": r"\brwth\b|aachen",
    "TU Berlin": r"\btu berlin\b|technische universität berlin|berlin",
    "Saarland University": r"saarland|saarbr(ü|ue)cken",
    "TU Dresden": r"\btu dresden\b|\btud\b|dresden",
    "KIT": r"\bkit\b|karlsruhe",
    "TU Darmstadt": r"darmstadt|\btuda\b",
    "University of Stuttgart": r"stuttgart",
}
CS = r"computer science|\bcs\b|informatik"
PROGRAMMES = {
    "TUM": {"M.Sc. Informatics": r"informatics|" + CS,
            "M.Sc. Data Engineering and Analytics": r"data engineering|\bdea\b"},
    "RWTH Aachen": {"M.Sc. Computer Science": CS, "M.Sc. Data Science": r"data science"},
    "TU Berlin": {"M.Sc. Computer Science": CS},
    "Saarland University": {"M.Sc. Computer Science": CS,
                            "M.Sc. Data Science and Artificial Intelligence":
                                r"data science|artificial intelligence|\bai\b|\bdsai\b"},
    "TU Dresden": {"M.Sc. Computer Science": CS},
    "KIT": {"M.Sc. Computer Science": CS + r"|informatics",
            "M.Sc. Computational and Data Science": r"computational|data science|\bcds\b"},
    "TU Darmstadt": {"M.Sc. Computer Science": CS,
                     "M.Sc. Artificial Intelligence and Machine Learning":
                         r"artificial intelligence|machine learning|\bai\b|\baiml\b"},
    "University of Stuttgart": {"M.Sc. Computer Science": CS},
}
# values the API accepts per key: a typo would otherwise match only the unscoped pages
KNOWN = {"university": set(UNIVERSITIES), "programme": {p for ps in PROGRAMMES.values() for p in ps},
         "stage": set(get_args(Stage)), "layer": set(get_args(Layer))}
# another institution in a covered city (LMU in Munich, FU or HU in Berlin, a Hochschule): the city
# name must not scope the question to the covered university, or the coverage refusal could not fire.
# ponytail: a short list of the usual same-city names; extend it when the long tail adds cities
OTHER_INSTITUTIONS = (r"\blmu\b|ludwig|humboldt|\b(fu|hu) berlin\b|freie universit|free university|hochschule"
                      r"|\bhtw\b|\bfh\b|applied sciences")


def matches(chunk: Chunk, filters: dict[str, list[str]]) -> bool:
    for key, allowed in filters.items():
        value = getattr(chunk, key)
        if value not in allowed and not (key in SCOPES and value is None):
            return False
    return True


def detect_filters(query: str) -> dict[str, list[str]]:
    """University and programme scope named in the question. A university whose
    programme is not named unambiguously keeps all its programmes, so a
    comparison across universities never drops one side."""
    text = query.lower()
    if re.search(OTHER_INSTITUTIONS, text):
        return {}
    unis = [u for u, pattern in UNIVERSITIES.items() if re.search(pattern, text)]
    if not unis:
        return {}
    programmes, narrowed = [], False
    for uni in unis:
        named = [p for p, pattern in PROGRAMMES[uni].items() if re.search(pattern, text)]
        narrowed |= len(named) == 1
        programmes += named if len(named) == 1 else list(PROGRAMMES[uni])
    filters = {"university": unis}
    if narrowed:
        filters["programme"] = sorted(set(programmes))
    return filters
