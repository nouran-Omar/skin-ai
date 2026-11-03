"""Rate limiting and request-identity helpers used by the public API."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

_HITS: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_LOCK = Lock()


def client_key(request: Request) -> str:
    # Use the peer address after Uvicorn's trusted proxy middleware has
    # normalized it. Never trust a client-supplied X-Forwarded-For value here.
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def rate_limit(request: Request, bucket: str, limit: int, window_seconds: int = 60) -> None:
    """Reject a client that exceeds `limit` calls to `bucket` in the window."""
    if limit < 1:
        return
    key = (bucket, client_key(request))
    now = time.monotonic()
    with _LOCK:
        hits = _HITS[key]
        while hits and hits[0] <= now - window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
        hits.append(now)
        if len(_HITS) > 4096:
            expired = [item for item, queue in _HITS.items() if not queue or queue[-1] <= now - window_seconds]
            for item in expired:
                _HITS.pop(item, None)
