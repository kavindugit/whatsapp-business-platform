"""
app/db/session.py
Database engine factory and session management.

Two separate engines:
  - app_runtime engine: used by all application code (no superuser, no BYPASSRLS)
  - migration engine:   used ONLY by Alembic CLI (migration_owner role)

Connection pooling:
  - psycopg async pool for the runtime engine
  - Connection context set transaction-locally (see tenant_context.py)
  - Pool settings are conservative for a single-server development stack

IMPORTANT:
  - Never use the migration engine in application request handlers
  - Never share a connection across requests (pool handles checkout/return)
  - Tenant context (app.tenant_id) is set per-transaction; never persisted in the pool
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def create_runtime_engine(settings: Settings) -> AsyncEngine:
    """
    Create the async SQLAlchemy engine for the app_runtime role.
    This is the ONLY engine used during normal request handling.
    """
    return create_async_engine(
        settings.database_url,
        echo=settings.is_development,   # Log SQL in development only
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,             # Detect stale connections
        pool_recycle=300,               # Recycle connections after 5 minutes
        connect_args={
            "connect_timeout": 10,
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Avoid lazy-load errors after commit
        autoflush=False,
        autocommit=False,
    )


# Module-level singletons, initialised in create_app()
_runtime_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(settings: Settings) -> None:
    """Initialise the database engine and session factory. Called once at startup."""
    global _runtime_engine, _session_factory
    _runtime_engine = create_runtime_engine(settings)
    _session_factory = create_session_factory(_runtime_engine)


def get_engine() -> AsyncEngine:
    if _runtime_engine is None:
        raise RuntimeError("Database not initialised. Call init_db() at startup.")
    return _runtime_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() at startup.")
    return _session_factory


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    FastAPI dependency: yield a raw async connection from the runtime engine.
    Used by tenant_transaction() which manages the transaction lifecycle.
    """
    engine = get_engine()
    async with engine.connect() as conn:
        yield conn


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yield a database session for control-plane operations
    (auth, admin) that do NOT require tenant-scoped RLS context.
    Transaction is committed/rolled back by the caller.
    """
    factory = get_session_factory()
    async with factory() as session:
        yield session
