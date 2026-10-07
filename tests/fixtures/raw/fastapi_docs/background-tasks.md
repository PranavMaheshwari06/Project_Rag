# Background Tasks

Sometimes an endpoint should return immediately while some follow-up work —
sending a confirmation email, writing an audit log — happens after the
response goes out. `BackgroundTasks` covers this without any extra
infrastructure.

## Running work after the response

Declare a parameter of type `BackgroundTasks` and register callables on it.
FastAPI runs them after the response has been sent, so the client never waits
for them.

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(message + "\n")

@app.post("/signup/")
def signup(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, f"new signup: {email}")
    return {"status": "ok"}
```

`add_task` takes the function plus whatever arguments it needs. The signup
response returns instantly; the log line is written afterwards, in the same
process. Both sync and async functions are accepted.

## Combining with dependencies

Dependencies can also receive `BackgroundTasks` and schedule work — useful
when the follow-up belongs to the shared logic (say, refreshing a cache entry
after any write) rather than one endpoint.

## When to reach for a real task queue

Background tasks run in the same process as the web server. That's perfect
for small, quick jobs, and exactly wrong for heavy work: a long-running task
ties up server resources, dies if the process restarts, and can't retry or be
distributed. If the work is CPU-heavy, must survive restarts, or needs
retries and monitoring, use a proper task queue such as Celery or RQ with a
message broker. The rule of thumb: if you'd be upset losing the job when the
pod restarts, it doesn't belong in `BackgroundTasks`.
