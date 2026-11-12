"""Agent tool loop with a scripted fake LLM and a fake retrieval pipeline: no
network, no key, no index build. Programme data is the committed verified
records and rule files, read through a fresh settings copy."""

import json

import pytest

from agent.loop import LAST_STEP, REPAIR, run_agent
from agent.tools import Toolbox
from core.config import load_settings
from eligibility.profile import Profile
from generation.prompt_builder import REFUSAL_TEXT
from schemas.common import Chunk, RetrievedChunk

KIT = "kit-m-sc-computer-science"


class FakeLLM:
    """Returns canned replies in order; records every message list it was sent."""

    available = True

    def __init__(self, *replies):
        self.replies, self.sent = [r if isinstance(r, str) else json.dumps(r) for r in replies], []

    def complete(self, messages, json_mode=False):
        assert json_mode
        self.sent.append([dict(m) for m in messages])
        return self.replies.pop(0)


def chunk(i: int, doc_id: str = "de/munich/residence-permit-study") -> Chunk:
    return Chunk(chunk_id=f"c{i}", doc_id=doc_id, source=doc_id, title=f"Page {i}", section_path="s",
                 url=f"https://example.org/{i}", text=f"Passage {i} says 11,904 euros.", token_count=8)


class FakePipeline:
    def __init__(self, score: float = 0.9):
        self.score, self.queries = score, []

    def search(self, query, mode="hybrid_rerank", top_k=None, **_):
        self.queries.append((query, mode, top_k))
        return [RetrievedChunk(chunk=chunk(i), rerank_score=self.score - i / 100) for i in range(1, top_k + 1)]


@pytest.fixture
def settings():
    return load_settings()


def toolbox(settings, profile=None, score=0.9):
    return Toolbox(settings, FakePipeline(score), profile, intake="winter", starting_year=2027)


def call(tool, **args):
    return {"tool": tool, "args": args}


def test_two_hop_answer_is_cited_and_traced(settings):
    llm = FakeLLM(call("search_sources", query="blocked account Munich"),
                  call("get_requirements", programme=KIT, fields=["min_total_ects"]),
                  {"answer": "You need 180 ECTS [4] and 11,904 euros in the blocked account [1]."})
    out = run_agent("ECTS for KIT CS and blocked account?", toolbox(settings), llm)
    assert out.stop_reason == "answered" and not out.refused and out.llm_calls == 3
    assert [s.tool for s in out.steps] == ["search_sources", "get_requirements"]
    assert out.steps[0].markers == [1, 2, 3] and out.steps[1].markers == [4]
    assert [c.marker for c in out.citations] == [1, 4]
    assert out.evidence[3].doc_id == "de/kit/cs-msc/programme"
    assert out.citations[1].url.startswith("https://")
    # the passages reached the model numbered, so its markers point at real slots
    assert "[4] KIT M.Sc. Computer Science" in llm.sent[2][-1]["content"]


def test_hallucinated_marker_alone_gives_the_refusal(settings):
    llm = FakeLLM(call("search_sources", query="x"), {"answer": "It is 5,000 euros [9]."})
    out = run_agent("q", toolbox(settings), llm)
    assert out.stop_reason == "uncited" and out.refused and out.text == REFUSAL_TEXT and not out.citations


def test_model_refusal_is_reported_as_refused(settings):
    out = run_agent("q", toolbox(settings), FakeLLM({"answer": REFUSAL_TEXT}))
    assert out.stop_reason == "refused" and out.refused


def test_step_budget_is_hard(settings):
    llm = FakeLLM(*[call("search_sources", query=f"q{i}") for i in range(3)])
    out = run_agent("q", toolbox(settings), llm, max_steps=3)
    assert out.stop_reason == "budget" and out.llm_calls == 3 and len(out.steps) == 2
    assert llm.sent[-1][-1]["content"] == LAST_STEP and not llm.replies


def test_two_bad_replies_stop_the_loop(settings):
    llm = FakeLLM("not json", "still not json")
    out = run_agent("q", toolbox(settings), llm)
    assert out.stop_reason == "bad_output" and out.llm_calls == 2
    assert llm.sent[1][-1]["content"] == REPAIR


def test_tool_errors_go_back_to_the_model(settings):
    llm = FakeLLM(call("browse_web", url="x"), call("get_requirements", programme="../etc"),
                  call("convert_grade", best="a", passing=50, obtained=70), {"answer": REFUSAL_TEXT})
    out = run_agent("q", toolbox(settings), llm)
    assert [s.ok for s in out.steps] == [False, False, False]
    assert "Tool error: unknown tool" in llm.sent[1][-1]["content"]
    assert "is not covered" in llm.sent[2][-1]["content"]


def test_weak_search_hits_add_no_evidence(settings):
    tb = toolbox(settings, score=settings.generation.refusal_threshold - 0.1)
    llm = FakeLLM(call("search_sources", query="Mars visa"), {"answer": "Yes [1]."})
    out = run_agent("q", tb, llm)
    assert out.steps[0].markers == [] and out.stop_reason == "uncited"


def test_repeated_passage_keeps_its_marker(settings):
    llm = FakeLLM(call("search_sources", query="a"), call("search_sources", query="a"), {"answer": "x [2]."})
    out = run_agent("q", toolbox(settings), llm)
    assert out.steps[1].markers == [1, 2, 3] and len(out.evidence) == 3


def test_eligibility_comes_from_the_engine_and_hides_profile_values(settings):
    profile = Profile(degree_country="India", total_credits="173.5", credit_unit="ECTS")
    llm = FakeLLM(call("check_eligibility", programme=KIT), {"answer": "The engine says no [2]."})
    out = run_agent("Do I qualify for KIT CS?", toolbox(settings, profile), llm)
    seen = llm.sent[1][-1]["content"]
    assert "Engine headline (report it as is, do not change it): does_not_meet_published_requirements" in seen
    assert "173.5" not in json.dumps(llm.sent)
    assert out.steps[0].ok and out.stop_reason == "answered"


def test_eligibility_without_a_profile_is_refused_to_the_model(settings):
    llm = FakeLLM(call("check_eligibility", programme=KIT), {"answer": REFUSAL_TEXT})
    out = run_agent("Do I qualify?", toolbox(settings), llm)
    assert not out.steps[0].ok and "no profile" in llm.sent[1][-1]["content"]


def test_convert_grade_tool(settings):
    r = toolbox(settings).call("convert_grade", {"best": 100, "passing": 50, "obtained": 75})
    assert r.ok and "2.50" in r.text and r.data == {"german": "2.5"}
    assert not toolbox(settings).call("convert_grade", {"best": 10, "passing": 4, "obtained": 2}).ok


def test_not_published_fields_are_said_not_cited(settings):
    r = toolbox(settings).call("get_requirements", {"programme": KIT, "fields": ["german"]})
    assert r.ok and "german: not published" in r.text and r.evidence == []
    assert not toolbox(settings).call("get_requirements", {"programme": KIT, "fields": ["salary"]}).ok


def test_fenced_json_reply_is_accepted(settings):
    llm = FakeLLM("```json\n" + json.dumps(call("search_sources", query="a")) + "\n```", {"answer": "y [1]."})
    assert run_agent("q", toolbox(settings), llm).stop_reason == "answered"
