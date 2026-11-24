"""In-process response cache for /answer: LRU with a TTL, one worker (a restart empties it, a second worker
would keep its own copy; a shared store is the upgrade).

The key is the question (case and spacing folded) plus the filters, hashed. The stored answer keeps no
`query` field, but its text can echo the question; it stays in memory for the TTL and is never logged.

The model, the prompt and the corpus are not in the key: all three are fixed for the life of the process. The corpus only changes through /ingest with a rebuild, which empties the cache, or through a
redeploy, which restarts the process. A key that changed any of them at runtime would need them in the key."""

import hashlib
import json
import threading
import time
from collections import OrderedDict

_now = time.time  # module-level so tests can drive the clock


def answer_key(query: str, filters: dict[str, list[str]] | None) -> str:
    # filter values are "any of", so their order does not change retrieval
    norm_filters = {k: sorted(v) for k, v in (filters or {}).items()}
    raw = json.dumps([" ".join(query.casefold().split()), norm_filters], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


class TTLCache:
    """max_entries <= 0 turns it off. `gen` counts clears: a caller reads it before building a value and passes
    it to `put`, so a value built from data that a clear made stale is dropped instead of stored."""

    def __init__(self, max_entries: int, ttl_s: float):
        self.max_entries, self.ttl_s = max_entries, ttl_s
        self._data: OrderedDict[str, tuple[float, object]] = OrderedDict()  # key -> (expires at, value)
        self._lock = threading.Lock()  # sync routes run in a thread pool
        self.gen = 0

    def get(self, key: str):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if entry[0] <= _now():
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return entry[1]

    def put(self, key: str, value, gen: int | None = None) -> None:
        if self.max_entries <= 0:
            return
        with self._lock:
            if gen is not None and gen != self.gen:
                return
            self._data[key] = (_now() + self.ttl_s, value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self.gen += 1
