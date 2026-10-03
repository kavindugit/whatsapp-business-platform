"""
app/core/errors.py
Centralised error handling: error envelope format, exception types, and
FastAPI exception handlers.

All error responses use the common envelope:
    {
        "error": {"code": "...", "message": "...", "details": [...]},
        "request_id": "server-generated-uuid"
    }

Stack traces, SQL queries, bound parameters, and credentials are NEVER included
in responses. They are logged at ERROR level with the request_id for correlation.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


# ── Error envelope schema ─────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorEnvelope(BaseModel):
    error: ErrorBody
    request_id: str


def make_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build a standardised JSON error response."""
    rid = request_id or str(uuid.uuid4())
    body = ErrorEnvelope(
        error=ErrorBody(code=code, message=message, details=details or []),
        request_id=rid,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


# ── Application exception types ───────────────────────────────────────────────


class AppError(Exception):
    """Base for all application-defined exceptions."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        self.message = message or self.__class__.message
        self.extra = kwargs
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "The requested resource was not found."


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"
    message = "Authentication is required."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"
    message = "The request conflicts with the current state of the resource."


class VersionConflictError(ConflictError):
    code = "VERSION_CONFLICT"
    message = "This record changed. Refresh and try again."


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "VALIDATION_ERROR"
    message = "The request contains invalid data."


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "RATE_LIMITED"
    message = "Too many requests. Please try again later."


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"
    message = "A required service is temporarily unavailable."


class TenantSuspendedError(ForbiddenError):
    code = "TENANT_SUSPENDED"
    message = "This workspace is suspended. Contact platform support."


class SeatLimitExceededError(ConflictError):
    code = "SEAT_LIMIT_EXCEEDED"
    message = "This workspace has reached its staff member limit."


# ── FastAPI exception handlers ────────────────────────────────────────────────


def _get_request_id(request: Request) -> str:
    """Extract request ID set by logging middleware, or generate a new one."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle all application-defined errors."""
    rid = _get_request_id(request)
    if exc.status_code >= 500:
        logger.error(
            "application_error",
            request_id=rid,
            code=exc.code,
            message=exc.message,
            exc_info=exc,
        )
    return make_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=rid,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard Starlette/FastAPI HTTP exceptions."""
    rid = _get_request_id(request)
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    # Never echo exc.detail if it might contain sensitive info — use generic messages
    safe_message = str(exc.detail) if exc.status_code < 500 else "An error occurred."
    return make_error_response(
        status_code=exc.status_code,
        code=code,
        message=safe_message,
        request_id=rid,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation errors."""
    rid = _get_request_id(request)
    details = []
    for error in exc.errors():
        loc = " → ".join(str(loc) for loc in error.get("loc", []) if loc != "body")
        details.append(ErrorDetail(field=loc or None, message=error["msg"]))
    return make_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="The request contains invalid data.",
        details=details,
        request_id=rid,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions. Logs the full error; returns a safe 500."""
    rid = _get_request_id(request)
    logger.exception(
        "unhandled_exception",
        request_id=rid,
        exc_info=exc,
    )
    return make_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again or contact support.",
        request_id=rid,
    )
