"""Hand-rolled tool loop with a hard step budget. Each step is one LLM call that
returns one JSON object: a tool call or the final answer. Tool results are added
to one numbered evidence list, so the final answer's [n] markers go through the
same citation mapping as one-shot RAG. JSON mode instead of native function
calling keeps generation/llm_client.py unchanged and provider-agnostic.

Stop reasons: answered | refused (the model gave the refusal text) | uncited (an
answer with no valid marker is replaced by the refusal) | budget (no answer
within max_steps calls) | bad_output (two unparseable replies in a row)."""

import json
import time
from typing import Literal

from pydantic import BaseModel

from agent.tools import TOOLS, Toolbox
from generation.citation_mapper import map_citations
from generation.prompt_builder import REFUSAL_TEXT
from schemas.answer import Citation
from schemas.common import Chunk

StopReason = Literal["answered", "refused", "uncited", "budget", "bad_output"]

SYSTEM = """Task: help students applying to English-taught master's programmes in Germany.
Read-only tools are available. Reply with exactly ONE JSON object and nothing else, either
  {{"tool": "<name>", "args": {{...}}}}   to call a tool, or
  {{"answer": "<text>"}}                  to finish.
Tools:
{tools}
Covered programme slugs: {programmes}
Rules:
- Use ONLY the numbered evidence passages the tools return; no outside knowledge.
- Every claim in the answer cites its passage with an inline marker like [1] or [3].
- Never decide eligibility yourself. If asked whether the user qualifies, call check_eligibility and report
  its headline as it is.
- A question with two parts usually needs two lookups; gather both before answering.
- If the evidence does not answer the question, answer exactly: "{refusal}\""""

LAST_STEP = "Tool budget used up. Reply now with {\"answer\": ...} using only the evidence above."
REPAIR = "Reply with one JSON object: {\"tool\": ..., \"args\": {...}} or {\"answer\": ...}."


class Step(BaseModel):
    n: int
    tool: str
    args: dict
    ok: bool
    summary: str  # first line of the tool's text
    markers: list[int]  # evidence numbers this step added or reused
    ms: float


class AgentAnswer(BaseModel):
    question: str
    text: str
    refused: bool
    stop_reason: StopReason
    citations: list[Citation]
    evidence: list[Chunk]
    steps: list[Step]
    llm_calls: int


def _parse(reply: str) -> dict | None:
    text = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    answer = obj.get("answer")
    if isinstance(answer, str) and (answer.strip() or "tool" not in obj):
        return {"answer": answer}  # an empty answer next to a tool call is not a final answer
    if isinstance(obj.get("tool"), str) and isinstance(obj.get("args", {}), dict):
        return {"tool": obj["tool"], "args": obj.get("args", {})}
    return None


def system_prompt(toolbox: Toolbox) -> str:
    tools = "\n".join(f"- {name}: {desc}" for name, (_, desc) in TOOLS.items())
    return SYSTEM.format(tools=tools, programmes=", ".join(toolbox.programmes), refusal=REFUSAL_TEXT)


def run_agent(question: str, toolbox: Toolbox, llm, max_steps: int | None = None) -> AgentAnswer:
    max_steps = toolbox.settings.agent.max_steps if max_steps is None else max_steps
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")
    messages = [{"role": "system", "content": system_prompt(toolbox)}, {"role": "user", "content": question}]
    evidence: list[Chunk] = []
    steps: list[Step] = []
    calls, bad_in_row = 0, 0

    def finish(text: str, reason: StopReason) -> AgentAnswer:
        cited, citations = map_citations(text, evidence) if reason == "answered" else (text, [])
        if reason == "answered" and text.strip() == REFUSAL_TEXT:
            reason = "refused"
        elif reason == "answered" and not citations:
            reason = "uncited"  # every answer is cited, or it is not given
        if reason != "answered":
            cited, citations = REFUSAL_TEXT, []
        return AgentAnswer(question=question, text=cited, refused=reason != "answered", stop_reason=reason,
                           citations=citations, evidence=evidence, steps=steps, llm_calls=calls)

    while calls < max_steps:
        if calls == max_steps - 1:
            messages.append({"role": "user", "content": LAST_STEP})
        reply = llm.complete(messages, json_mode=True)
        calls += 1
        messages.append({"role": "assistant", "content": reply})
        action = _parse(reply)
        if action is None:
            bad_in_row += 1
            if bad_in_row == 2:
                return finish(REFUSAL_TEXT, "bad_output")
            messages.append({"role": "user", "content": REPAIR})
            continue
        bad_in_row = 0
        if "answer" in action:
            return finish(action["answer"], "answered")
        if calls == max_steps:
            break  # a tool call on the last allowed step: no answer within budget
        t0 = time.perf_counter()
        result = toolbox.call(action["tool"], action["args"])
        markers, passages = [], []
        for chunk in result.evidence:
            known = next((i for i, c in enumerate(evidence, 1) if c.chunk_id == chunk.chunk_id), None)
            if known is None:
                evidence.append(chunk)
                known = len(evidence)
            markers.append(known)
            passages.append(f"[{known}] {chunk.title} — {chunk.section_path}\n{chunk.text}")
        steps.append(Step(n=len(steps) + 1, tool=action["tool"], args=action["args"], ok=result.ok,
                          summary=result.text.splitlines()[0] if result.text else "", markers=markers,
                          ms=round((time.perf_counter() - t0) * 1000, 1)))
        observation = "\n\n".join([("" if result.ok else "Tool error: ") + result.text, *passages])
        messages.append({"role": "user", "content": f"Result of {action['tool']}:\n{observation}"})
    return finish(REFUSAL_TEXT, "budget")
