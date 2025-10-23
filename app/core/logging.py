from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


def bind_request_id(request_id: str) -> None:
    """
    Bind the request identifier to the structlog context for downstream log records.
    """

    request_id_ctx_var.set(request_id)
    structlog.contextvars.bind_contextvars(request_id=request_id)


def clear_request_id() -> None:
    """Remove the request identifier from the log context."""

    request_id_ctx_var.set("")
    structlog.contextvars.clear_contextvars()


def configure_logging(level: int = logging.INFO) -> None:
    """Configure standard logging and structlog for JSON output."""

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Silence noisy third-party loggers by default.
    for name in ("uvicorn.error", "uvicorn.access", "sqlalchemy.engine", "aiosqlite"):
        logging.getLogger(name).setLevel(level)
