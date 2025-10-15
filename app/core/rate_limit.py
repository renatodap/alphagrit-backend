import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.core.errors import error_envelope
from app.api.v1.deps.auth import get_lang
from app.shared.i18n.localize import t


class InMemoryRateLimiter:
    def __init__(self, max_per_minute: int = 120) -> None:
        self.max_per_minute = max_per_minute
        self.hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

    def allow(self, key: Tuple[str, str]) -> bool:
        now = time.time()
        bucket = self.hits[key]
        # remove entries older than 60s
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= self.max_per_minute:
            return False
        bucket.append(now)
        return True


def init_rate_limiter(app: FastAPI, max_per_minute: int = 120) -> None:
    limiter = InMemoryRateLimiter(max_per_minute=max_per_minute)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        lang = await get_lang(request.headers.get("accept-language"))  # type: ignore[arg-type]
        if not limiter.allow((client_ip, path)):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_envelope("RATE_LIMITED", t(lang, "errors.rate_limited")),
            )
        return await call_next(request)
