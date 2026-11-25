"""Server-sent events for a sync event generator, with the same accounting as a normal request.

Starlette iterates a sync generator with one thread-pool call per item. Each call runs in a copy of the request's
context, taken while the logging middleware's usage tracker (with the daily-cap hook) and the request deadline were
set, so LLM calls made while streaming are counted on that same tracker, capped and bounded by the deadline. Two
things do not carry over: a contextvar set inside the generator (each item runs in a fresh copy, so resetting it
raises ValueError), and the middleware's access line, which is written when the response starts, before any call
is made. So the generator writes the stream's own line when it ends, from the same tracker.

If the client disconnects, Starlette (under the ASGI 2.3 that uvicorn reports) stops pulling items, so no further
call is made; one already running finishes first. It never closes the generator, which would leave the line unwritten
until some later garbage collection, so the response closes it as its background task."""

import json
import logging
import time
import traceback
from collections.abc import Callable, Iterator
from pathlib import Path

from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from core.exceptions import AppError
from core.logging import log_event
from core.metrics import current_usage

log = logging.getLogger("api.access")

Event = tuple[str, dict]  # (event name, JSON-able data)
UNEXPECTED = "something went wrong; try again"


def _frame(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, default=str)}\n\n"


def sse(request: Request, events: Callable[[], Iterator[Event]]) -> StreamingResponse:
    """Stream `events()` as SSE. An AppError ends the stream with an `error` event carrying its message; any
    other exception with a fixed message (it may echo the question). The final `answer` event gets `usage`.
    The stream's log line adds whatever the route attached with `trace()`."""
    path = request.url.path

    def body() -> Iterator[str]:
        usage = current_usage()  # the middleware's tracker for this request
        start, steps, end = time.perf_counter(), 0, {}
        try:
            for name, data in events():
                steps += name == "step"
                if name == "answer":
                    data["usage"] = {"llm_calls": usage.calls, "prompt_tokens": usage.prompt_tokens,
                                     "completion_tokens": usage.completion_tokens, "model": usage.model}
                    end = {k: data.get(k) for k in ("answered_by", "refused", "refusal_reason", "cached")}
                yield _frame(name, data)
        except GeneratorExit:  # closed before its end: the client hung up
            end = end or {"error": "ClientDisconnected"}
            raise
        except AppError as e:
            end = {"error": type(e).__name__}
            yield _frame("error", {"detail": e.message})
        except Exception as e:  # the message may carry the question: log the type and the place, never the text
            places = [f"{Path(f.filename).name}:{f.lineno} {f.name}" for f in traceback.extract_tb(e.__traceback__)]
            end = {"error": type(e).__name__, "at": places[-3:]}
            yield _frame("error", {"detail": UNEXPECTED})
        finally:
            log_event(log, "stream", path=path, duration_ms=round((time.perf_counter() - start) * 1000, 1),
                      llm_calls=usage.calls, prompt_tokens=usage.prompt_tokens,
                      completion_tokens=usage.completion_tokens, model=usage.model, steps=steps,
                      **request.state.trace, **end)

    stream = body()
    return StreamingResponse(stream, media_type="text/event-stream", background=BackgroundTask(stream.close),
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
