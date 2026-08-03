# Query Parameters

When you declare function parameters that are not part of the path, FastAPI
interprets them as query parameters. The values come from the key-value pairs
after the `?` in the URL, and FastAPI converts and validates them using the
type annotations on your function signature.

## Declaring query parameters

Any function argument with a default value that does not appear in the route
path becomes a query parameter. The type annotation drives parsing: an `int`
annotation means the raw string from the URL is converted to an integer before
your function runs.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/")
def list_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

A request to `/items/?skip=20&limit=5` calls the function with `skip=20` and
`limit=5` as real integers. If the client sends `?skip=abc`, FastAPI rejects
the request with a 422 response that pinpoints the offending parameter, so you
never see malformed input inside the handler.

## Optional parameters and defaults

To make a query parameter optional, give it a default of `None` and annotate
it as optional. The handler then has to deal with the missing case explicitly,
which keeps the "was it provided?" logic visible instead of buried in
framework magic.

```python
@app.get("/items/{item_id}")
def read_item(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

Here `q` is an optional query parameter: requests to `/items/foo` and
`/items/foo?q=search-term` are both valid. Any parameter with a default value
is optional; the default is used when the client omits it. On older Python
versions you can write `Optional[str] = None` from `typing` — the behaviour is
identical.

## Required query parameters

If you declare a query parameter without a default value, it becomes required.
A request that omits it fails validation with a clear error message naming the
missing field.

```python
@app.get("/search/")
def search(term: str, page: int = 1):
    return run_search(term, page)
```

`term` is required because it has no default; `page` is optional and defaults
to 1. Mixing required and optional query parameters in one signature is
normal and encouraged — the signature documents the contract.

## Type conversion and booleans

Query values arrive as strings, and FastAPI converts them based on the
annotation. Booleans are notably forgiving: `?flag=1`, `?flag=true`,
`?flag=on` and `?flag=yes` all parse to `True`. Enums, floats, UUIDs and
datetimes work the same way — annotate the parameter and let the framework
reject anything that doesn't parse rather than writing manual casts.
