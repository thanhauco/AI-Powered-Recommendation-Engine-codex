from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.api import api_router
from app.core import bind_request_id, configure_logging, settings
from app.core.cache import close_redis_client
from app.core.database import dispose_engine
from app.core.logging import clear_request_id

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request identifier to each inbound request."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        bind_request_id(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            clear_request_id()
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""

    log_level = logging.DEBUG if settings.debug else logging.INFO
    configure_logging(level=log_level)
    logger.info(
        "application.startup",
        environment=settings.environment,
    )
    try:
        yield
    finally:
        await close_redis_client()
        await dispose_engine()
        logger.info("application.shutdown")


def get_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/", summary="Service root")
    async def root() -> dict[str, str]:
        """Return a minimal welcome document."""

        return {"message": settings.app_name, "environment": settings.environment}

    return app


app = get_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
