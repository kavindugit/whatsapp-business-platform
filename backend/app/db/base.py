"""
app/db/base.py
SQLAlchemy declarative base and shared model conventions.

Conventions:
  - UUID v4 primary keys generated server-side
  - UTC timezone-aware timestamps with server defaults
  - created_at / updated_at on all mutable tables
  - Table names are explicit (no auto-pluralisation surprises)
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


def new_uuid() -> uuid.UUID:
    """Generate a new UUID v4 for use as a primary key."""
    return uuid.uuid4()
