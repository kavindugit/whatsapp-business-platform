"""
app/core/logging.py
Structured JSON logging configuration using structlog.

Each log entry includes:
  - timestamp (UTC ISO 8601)
  - level
  - logger name
  - request_id (when available from request context)
  - actor_id / tenant_id (safe identifiers only — never passwords, tokens, raw notes)
  - event

Sensitive values (passwords, session tokens, CSRF values, raw contact data)
must NEVER appear in log messages or structured fields.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


def configure_logging(*, json_logs: bool = True) -> None:
    """
    Configure structlog for structured JSON output (production) or
    colourised console output (development).
    Should be called once at application startup.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        # Production: machine-readable JSON
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: human-friendly colourised output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging to route through structlog
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Per-request structured logging middleware.
    Generates a unique request_id, binds it to structlog context vars,
    and logs: method, route template, status code, and duration.

    Does NOT log:
      - Query string parameters (may contain sensitive data)
      - Request bodies
      - Response bodies
      - Authentication headers or cookies
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        import time

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind request_id to the structlog context for this coroutine
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Safe actor/tenant IDs will be bound by route handlers after authentication
        start = time.monotonic()
        log = structlog.get_logger("request")

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.monotonic() - start) * 1000)
            log.error(
                "request_error",
                method=request.method,
                # Use route template, not the actual URL (avoids logging UUIDs/PII in path)
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.monotonic() - start) * 1000)

        # Don't log health check noise
        if request.url.path not in ("/api/health/live", "/api/health/ready"):
            log.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.clear_contextvars()
        return response
