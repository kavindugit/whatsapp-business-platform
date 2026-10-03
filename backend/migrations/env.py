"""
migrations/env.py
Alembic migration environment.

Key design decisions (W1-030):
  - Uses MIGRATION_DATABASE_URL (migration_owner role), NOT DATABASE_URL (app_runtime)
  - Runtime application never uses this file or these credentials
  - Runs synchronously (psycopg sync driver) as Alembic does not support async
  - Imports all models to ensure they are registered with Base.metadata
  - Does not auto-import future weeks' models; add them explicitly when needed
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Load alembic.ini logging config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import all models so their metadata is available to Alembic ───────────────
# Add new model imports here when new modules are implemented.
# DO NOT import future-week models until those weeks begin.
from app.db.base import Base  # noqa: E402

# Week 1 models — all registered with Base.metadata for Alembic autogenerate
from app.db.models.users import User, AuthSession  # noqa: F401, E402
from app.db.models.tenants import Tenant, TenantMembership  # noqa: F401, E402
from app.db.models.plans import Package, PackageVersion, Subscription  # noqa: F401, E402
from app.db.models.settings import BusinessSettings  # noqa: F401, E402
from app.db.models.contacts import Contact  # noqa: F401, E402
from app.db.models.audit import PlatformAuditEvent, TenantAuditEvent  # noqa: F401, E402

target_metadata = Base.metadata

# ── Database URL ───────────────────────────────────────────────────────────────
# ALWAYS use MIGRATION_DATABASE_URL (migration_owner role), never DATABASE_URL.
# This is enforced here; the application never reads this variable.
def get_migration_url() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "MIGRATION_DATABASE_URL is required for migrations. "
            "Set it in your .env file (migration_owner role credentials)."
        )
    # Alembic uses synchronous psycopg; replace async driver prefix if present
    # The dialect for psycopg v3 sync is `postgresql+psycopg`
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


def run_migrations_offline() -> None:
    """Run migrations without a live database connection (SQL script generation)."""
    url = get_migration_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    url = get_migration_url()
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            # Render each migration in its own transaction for safety
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
