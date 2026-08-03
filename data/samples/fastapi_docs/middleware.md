# Middleware and CORS

Middleware wraps every request/response pair that flows through the
application. It's the right place for cross-cutting concerns — timing,
request IDs, compression — that shouldn't be repeated in every endpoint.

## Writing custom middleware

The lightest way is the `@app.middleware("http")` decorator: an async
function receiving the request and a `call_next` callable. Whatever you do
before `call_next` runs before routing; whatever you do after runs on the way
out.

```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = str(elapsed)
    return response
```

This middleware measures how long each request takes to process and reports
it in a custom `X-Process-Time` response header — a cheap way to spot slow
endpoints without touching any handler code.

## Middleware order

Middleware added last runs first on the way in and last on the way out; the
stack is an onion. If you have a request-ID middleware and a logging
middleware that wants to include the ID, add the logging middleware first and
the request-ID middleware after it.

## Enabling CORS

Browsers block cross-origin requests unless the server opts in. To enable
CORS, add the built-in `CORSMiddleware` and list the origins allowed to call
your API.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.example.com", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

With this in place the browser's preflight `OPTIONS` requests are answered
automatically and the `Access-Control-Allow-Origin` header is set on
responses to the listed origins. Use explicit origins in production;
`allow_origins=["*"]` is fine for a public read-only API but incompatible
with `allow_credentials=True` — browsers reject that combination.

## When middleware is the wrong tool

Anything that needs per-endpoint variation — auth scopes, response shaping —
belongs in dependencies, not middleware. Middleware can't easily know which
route matched, and stuffing route-specific branching into it turns the onion
into spaghetti.
