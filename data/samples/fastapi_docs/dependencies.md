# Dependencies

FastAPI's dependency injection system lets you declare shared logic —
database sessions, auth checks, pagination parameters — once, and have the
framework provide it to every endpoint that asks for it. A dependency is just
a callable; `Depends` tells FastAPI to call it and hand the result to your
function.

## What Depends does

Declare a parameter whose default is `Depends(some_callable)`. Before your
endpoint runs, FastAPI calls the dependency (resolving its own parameters the
same way, recursively) and passes the return value in.

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def pagination(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}

@app.get("/items/")
def list_items(page: dict = Depends(pagination)):
    return fake_db[page["skip"] : page["skip"] + page["limit"]]
```

The dependency's own parameters (`skip`, `limit`) are pulled from the query
string exactly as if they were declared on the endpoint. Ten endpoints can
share one pagination contract without repeating it.

## Sharing a database session

The classic use case is one database session per request, closed no matter
what. Write the dependency as a generator: code before `yield` runs before
the endpoint, code after `yield` runs at cleanup time, even if the endpoint
raised.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/orders/{order_id}")
def read_order(order_id: int, db: Session = Depends(get_db)):
    return db.get(Order, order_id)
```

Every endpoint that declares `db: Session = Depends(get_db)` gets a fresh
session, and the `finally` block guarantees it's returned to the pool. This
is how you share database connections between endpoints safely — share the
factory, not the session.

## Sub-dependencies and per-request caching

Dependencies can depend on other dependencies, forming a tree that FastAPI
resolves for you. If the same dependency appears several times in one
request's tree, it is called once and the result is cached for that request.
Pass `use_cache=False` to `Depends` when you genuinely need it re-executed.

## Class dependencies

Any callable works, so classes are fine too: `Depends(CommonParams)` calls
the constructor and gives you a typed object instead of a dict, which plays
nicer with editors and mypy.
