"""POST /chat/stream: one question, answered by one-shot RAG, the agent, or `auto` (one-shot, then the agent if it
refuses), streamed as server-sent events. Events: `sources` (one-shot's retrieved passages), `escalated`, `step`
(one agent tool call), `answer` (the final answer, cited or refused), `error`. The contract is in
docs/production-layer-spec.md."""

from collections.abc import Iterator
from datetime import date

from fastapi import APIRouter, Depends, Request

from agent.loop import AgentAnswer, agent_events, should_escalate
from agent.tools import Toolbox
from api.cache import TTLCache, answer_key
from api.dependencies import get_llm_client, get_retrieval_pipeline
from api.limits import limit_llm
from api.middleware.logging_mw import trace
from api.routes.answer import answer_steps
from api.stream import Event, sse
from core.config import get_settings
from core.exceptions import BadRequestError, ServiceUnavailableError
from schemas.answer import AnswerResponse
from schemas.chat import ChatRequest

router = APIRouter(dependencies=[Depends(limit_llm)])

# agent stop reasons a retry can change: not cached
AGENT_NOT_CACHED = {"uncited", "guardrail", "budget", "bad_output"}


def oneshot_events(body: ChatRequest, request: Request, cache: TTLCache | None) -> Iterator[Event]:
    for item in answer_steps(body.query, body.filters, request.state.request_id, cache, body.user_source):
        if isinstance(item, AnswerResponse):
            trace(request, stages=item.latency_ms)  # for the stream's own log line
            yield "answer", {"answered_by": "oneshot", "text": item.answer, "refused": item.refused,
                             "refusal_reason": item.refusal_reason,
                             "citations": [c.model_dump() for c in item.citations], "cached": item.cached}
        else:
            yield "sources", {"chunks": [{"chunk_id": rc.chunk.chunk_id, "doc_id": rc.chunk.doc_id,
                                          "title": rc.chunk.title, "section_path": rc.chunk.section_path,
                                          "url": rc.chunk.url, "rerank_score": rc.rerank_score} for rc in item]}


def agent_answer(out: AgentAnswer) -> dict:
    reason = {"answered": None, "refused": "model"}.get(out.stop_reason, out.stop_reason)
    return {"answered_by": "agent", "text": out.text, "refused": out.refused, "refusal_reason": reason,
            "citations": [c.model_dump() for c in out.citations], "cached": False}


def agent_stream(body: ChatRequest, cache: TTLCache | None) -> Iterator[Event]:
    llm = get_llm_client()
    if not llm.available:
        raise ServiceUnavailableError("the agent needs the language model, which is not configured here")
    key = answer_key(body.query, body.filters, mode="agent")
    if cache is not None and (hit := cache.get(key)) is not None:
        yield "answer", {**hit, "citations": [dict(c) for c in hit["citations"]], "cached": True}
        return
    gen = cache.gen if cache is not None else None
    toolbox = Toolbox(get_settings(), get_retrieval_pipeline(), body.profile, as_of=date.today(),
                      intake=body.intake, starting_year=body.starting_year)
    for event in agent_events(body.query, toolbox, llm):
        if isinstance(event, AgentAnswer):
            data = agent_answer(event)
            # a crashed tool may work next time, so such a run is not kept; the model's own bad arguments are
            if cache is not None and event.stop_reason not in AGENT_NOT_CACHED and not toolbox.crashed:
                cache.put(key, {**data, "citations": [dict(c) for c in data["citations"]]}, gen)
            yield "answer", data
        else:
            yield "step", event.model_dump()


def auto_events(body: ChatRequest, request: Request, cache: TTLCache | None) -> Iterator[Event]:
    """One-shot first; the agent only when that outcome is worth its calls (agent.loop.should_escalate). A question
    with a profile goes straight to the agent: one-shot cannot see the profile, so it answers that the student's
    qualifications are unknown, and an answer is never escalated."""
    if body.profile is not None and get_llm_client().available:
        yield from agent_stream(body, cache)
        return
    top = 0.0
    for name, data in oneshot_events(body, request, cache):
        if name == "sources" and data["chunks"]:
            top = data["chunks"][0]["rerank_score"] or 0.0  # the score the refusal gate looked at
        if (name == "answer" and get_llm_client().available
                and not body.filters and body.user_source is None  # the agent sees neither
                and should_escalate(data["refusal_reason"], top, get_settings().agent.escalate_min_score)):
            yield "escalated", {"refusal_reason": data["refusal_reason"]}
            yield from agent_stream(body, cache)
        else:
            yield name, data


@router.post("/chat/stream")
def chat_stream(body: ChatRequest, request: Request):
    trace(request, mode=body.mode, query_len=len(body.query))
    if body.user_source is not None:
        limit = get_settings().generation.user_source_max_chars
        if len(body.user_source) > limit:
            raise BadRequestError(f"the pasted text is longer than {limit} characters")
        trace(request, user_source_len=len(body.user_source))
    cache =None if body.profile is not None else request.app.state.answer_cache  # a profile is never cached
    if body.mode == "agent":
        return sse(request, lambda: agent_stream(body, cache))
    run = auto_events if body.mode == "auto" else oneshot_events
    return sse(request, lambda: run(body, request, cache))
