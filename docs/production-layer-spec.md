# Production layer: the chat stream contract

`POST /chat/stream` answers one question and streams the process as server-sent events (SSE). It is what the
chat UI calls. `POST /answer` stays as the plain JSON version of one-shot.

## Request

```json
{
  "query": "What is the semester fee at TUM?",
  "mode": "oneshot",
  "filters": {"university": ["TUM"]},
  "profile": null,
  "profile_confirmed": false,
  "intake": null,
  "starting_year": null
}
```

| field | meaning |
|---|---|
| `query` | 1-1000 characters. |
| `mode` | `oneshot`: retrieve, then one LLM call (at most one repair call). `agent`: the tool loop, up to 6 LLM calls. `auto`: one-shot first, then the agent if one-shot refused (rule below), so at most 8 calls. Default `oneshot`. |
| `filters` | Optional metadata filters for one-shot retrieval (`university`, `programme`, `stage`, `layer`; values are "any of"). The agent chooses its own lookups and ignores them. |
| `profile` | Optional student profile (the `/eligibility/check` schema). Used only by the agent's `check_eligibility` tool, whose verdict the model reads. The profile itself never goes to the model and is never logged or cached. |
| `profile_confirmed` | Must be `true` when a profile is sent: a parsed draft is used only after the student confirms it. |
| `intake`, `starting_year` | Optional, for deadline checks in `check_eligibility`. |

## Before the stream starts: plain HTTP errors

| status | when |
|---|---|
| 422 | invalid request (including a profile without `profile_confirmed: true`) |
| 429 | per-client limit or the global daily LLM-call cap; body `{"detail", "request_id"}`, header `Retry-After` |
| 400 / 411 / 413 | a malformed `Content-Length`, a missing one, or a body over the size cap |

## The stream

`Content-Type: text/event-stream`. Each event is `event: <name>` plus one `data:` line of JSON. The response
header `x-request-id` identifies the request in the logs.

| event | mode | data |
|---|---|---|
| `sources` | oneshot, auto | `{"chunks": [{chunk_id, doc_id, title, section_path, url, rerank_score}]}` (the retrieved passages, best first) |
| `escalated` | auto | `{"refusal_reason": "model"}`: one-shot refused for this reason and the agent is starting. The one-shot refusal is not sent as an `answer`. |
| `step` | agent, auto | one tool call: `{n, tool, args, ok, summary, markers, ms}`; `markers` are the evidence numbers the step added or reused. They number the agent's own evidence, not the `sources` list. |
| `answer` | all | the final answer, always the last event of a successful stream (below) |
| `error` | all | `{"detail": "<message>"}`; ends the stream. Sent when the daily cap is reached mid-run, the request deadline passes, the LLM provider fails, or the agent is asked for with no LLM configured. An unexpected failure says only "something went wrong; try again". |

Order: one-shot sends `sources` as soon as retrieval ends, then `answer` when the model is done; the agent sends
zero or more `step` then `answer`; `auto` sends `sources`, then either `answer`, or `escalated`, zero or more
`step` and `answer`. Every stream that is read to its end has exactly one `answer` or one `error` as its last
event. If the client disconnects, no further LLM call is made (one already running finishes).

### When `auto` escalates

| one-shot outcome | escalates | why |
|---|---|---|
| answered (a partial answer included) | no | the cheap path worked |
| `model` or `uncited` refusal | yes | mostly retrieval misses, which the agent's own lookups can recover |
| `gate` refusal, best score 0.02 or more | yes | in scope, but the passages ranked low |
| `gate` refusal, best score under 0.02 | no | out of scope; six calls would be spent to say so |
| `guardrail` refusal | no | a possible injection must not get a tool loop |
| no LLM configured | no | the agent needs it |

### `answer`

```json
{
  "answered_by": "agent",
  "text": "The semester fee is 85 EUR [1].",
  "refused": false,
  "refusal_reason": null,
  "citations": [{"marker": 1, "chunk_id": "...", "url": "https://...", "title": "...", "section_path": "..."}],
  "cached": false,
  "usage": {"llm_calls": 2, "prompt_tokens": 1830, "completion_tokens": 64, "model": "gemini-3.8-flash"}
}
```

- Every `[n]` in `text` has a matching citation. An answer that cannot be cited is not given: `refused` is
  `true`, `text` is the refusal sentence and `citations` is empty.
- `refusal_reason`: `gate` (no passage scored high enough), `model` (the model said the evidence does not answer
  it), `uncited` (no valid citation after one repair), `guardrail` (the answer repeated the system prompt),
  `extractive` (no LLM configured and no sentence matched); agent only: `budget` (no answer within 6 calls),
  `bad_output` (two unreadable replies in a row).
- `cached: true` means this answer came from the in-memory cache, with no retrieval or LLM call of its own
  (`usage.llm_calls` is 0, except in `auto` when the one-shot stage before it was not cached). Cached: answers and
  `gate`/`model`/`extractive` refusals, for 24 h, per stage (one-shot or agent). Never cached: a request with a
  profile, a refusal that a retry could change (`uncited`, `guardrail`, `budget`, `bad_output`), or an agent run in
  which a tool crashed. A cached agent answer comes with no `step` events.

## Logs

Besides the per-request access line (written when the stream starts, so its LLM numbers are zero), each stream
writes one `stream` line when it ends: request id, mode, whether it escalated, who answered, refused and refusal
reason, cached, one-shot stage times, number of agent steps, LLM calls, tokens, model, duration, and the error if it failed (`ClientDisconnected` if the client left; an
unexpected error also names the code location). No question text, profile value or client address is logged.
