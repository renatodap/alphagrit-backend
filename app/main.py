from contextlib import asynccontextmanager
from typing import AsyncIterator

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import init_error_handlers
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import init_rate_limiter
import uuid


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# CORS: allow frontend origins to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability and resilience
init_error_handlers(app)
init_rate_limiter(app, max_per_minute=settings.rate_limit_per_minute)

log = get_logger(__name__)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    request_id = str(uuid.uuid4())
    # attach request id to headers for tracing
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        client=getattr(request.client, "host", None),
        request_id=request_id,
    )
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"ready": True}


app.include_router(api_router, prefix="/api/v1")
