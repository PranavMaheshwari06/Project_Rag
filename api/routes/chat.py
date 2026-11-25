"""POST /chat/stream: one question, answered by one-shot RAG or the agent, streamed as server-sent events.
Events: `sources` (one-shot's retrieved passages), `step` (one agent tool call), `answer` (the final answer,
cited or refused), `error`. The contract is in docs/production-layer-spec.md."""

from collections.abc import Iterator
from datetime import date

from fastapi import APIRouter, Depends, Request

from agent.loop import AgentAnswer, agent_events
from agent.tools import Toolbox
from api.cache import TTLCache, answer_key
from api.dependencies import get_llm_client, get_retrieval_pipeline
from api.limits import limit_llm
from api.middleware.logging_mw import trace
from api.routes.answer import answer_steps
from api.stream import Event, sse
from core.config import get_settings
from core.exceptions import ServiceUnavailableError
from schemas.answer import AnswerResponse
from schemas.chat import ChatRequest

router = APIRouter(dependencies=[Depends(limit_llm)])

# agent stop reasons a retry can change: not cached
AGENT_NOT_CACHED = {"uncited", "guardrail", "budget", "bad_output"}


def oneshot_events(body: ChatRequest, request_id: str, cache: TTLCache | None) -> Iterator[Event]:
    for item in answer_steps(body.query, body.filters, request_id, cache):
        if isinstance(item, AnswerResponse):
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


@router.post("/chat/stream")
def chat_stream(body: ChatRequest, request: Request):
    trace(request, mode=body.mode, query_len=len(body.query))
    cache = None if body.profile is not None else request.app.state.answer_cache  # a profile is never cached
    rid = request.state.request_id
    events = (lambda: oneshot_events(body, rid, cache)) if body.mode == "oneshot" else (lambda: agent_stream(body, cache))
    return sse(request, events)
