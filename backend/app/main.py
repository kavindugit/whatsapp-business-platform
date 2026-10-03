"""
app/main.py
FastAPI application factory.

Create the app with create_app() — uvicorn is configured to call this
via --factory flag: uvicorn app.main:create_app --factory

Startup sequence:
  1. Load and validate configuration
  2. Configure structured logging
  3. Initialise database engine
  4. Register middleware (logging, CORS)
  5. Register exception handlers
  6. Mount routers
  7. Add health endpoints

No migrations run on startup. Run: docker exec wbp-api python -m alembic upgrade head
"""

from __future__ import annotations

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.db.session import init_db

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """
    Application factory. Returns a configured FastAPI instance.
    Called by uvicorn with --factory flag.
    """
    settings = get_settings()

    # 1. Configure logging first so startup errors are structured
    configure_logging(json_logs=settings.is_production)

    # 2. Create FastAPI app
    app = FastAPI(
        title="WhatsApp Business Platform",
        version="0.1.0",
        # Disable automatic /docs and /redoc in production
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None if settings.is_production else "/api/redoc",
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )

    # 3. Store settings on app state for access in lifespan/dependencies
    app.state.settings = settings

    # 4. Initialise database
    init_db(settings)

    # 5. CORS middleware
    # Only allow configured origins — no wildcard credentialed CORS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # 6. Request logging middleware (adds request_id, logs method/path/status/duration)
    app.add_middleware(RequestLoggingMiddleware)

    # 7. Exception handlers
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 8. Health endpoints (mounted before API prefix so they work through Vite proxy)
    _register_health_routes(app)

    # 9. API routers (registered as modules are implemented)
    from app.modules.auth.router import router as auth_router

    app.include_router(auth_router, prefix=settings.api_prefix)

    # Tenancy router — Week 1 Day 4
    from app.modules.tenancy.router import router as tenancy_router

    app.include_router(tenancy_router, prefix=settings.api_prefix)

    # Plans router — Week 1 Day 4
    from app.modules.plans.router import router as plans_router

    app.include_router(plans_router, prefix=settings.api_prefix)

    # Contacts router — Week 1 Day 4
    from app.modules.contacts.router import router as contacts_router

    app.include_router(contacts_router, prefix=settings.api_prefix)

    logger.info(
        "app_started",
        env=settings.app_env,
        label=settings.app_label,
        api_prefix=settings.api_prefix,
    )

    return app


def _register_health_routes(app: FastAPI) -> None:
    """Register health check endpoints outside the API prefix."""
    import sqlalchemy as sa

    from app.core.config import get_settings
    from app.db.session import get_engine

    @app.get("/api/health/live", tags=["health"], include_in_schema=False)
    async def liveness() -> dict[str, str]:
        """
        Process liveness check.
        Returns 200 if the process is running.
        Does NOT check external dependencies (database, Redis).
        Does NOT return any configuration values or secrets.
        """
        return {"status": "ok"}

    @app.get("/api/health/ready", tags=["health"], include_in_schema=False)
    async def readiness() -> dict[str, str]:
        """
        Readiness check.
        Returns 200 only if both the database and Redis are reachable.
        Returns 503 if either dependency is unavailable.
        Does NOT return connection strings, credentials, or diagnostic details.
        """
        from fastapi import status as http_status
        from fastapi.responses import JSONResponse

        cfg = get_settings()
        errors: list[str] = []

        # Check PostgreSQL
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute(sa.text("SELECT 1"))
        except Exception:
            errors.append("database")

        # Check Redis
        try:
            client = aioredis.from_url(cfg.redis_url, socket_connect_timeout=2)
            await client.ping()
            await client.aclose()
        except Exception:
            errors.append("redis")

        if errors:
            return JSONResponse(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unavailable", "failing": errors},
            )

        return {"status": "ready"}
