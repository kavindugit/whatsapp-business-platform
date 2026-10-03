"""
app/db/models/contacts.py
Tenant-owned model: Contact.
Protected by PostgreSQL Row-Level Security.

Key rules (W1-022):
- Phone numbers stored as E.164 normalised strings or null
- Partial unique index: same phone allowed across tenants; duplicate blocked within one tenant (active only)
- Composite unique (tenant_id, id) enables safe composite FK references from future tables
- No hard-delete: use archive/restore workflow
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_e164: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    preferred_lang: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Composite unique for future composite FK references
        # (tenant_id, id) declared as unique — enforced in migration
        Index("ix_contacts_tenant_id", "tenant_id"),
        Index("ix_contacts_tenant_updated", "tenant_id", "updated_at"),
        # Partial unique index for phone uniqueness within a tenant (active contacts only)
        # Defined with WHERE clause in migration SQL — SQLAlchemy partial index:
        Index(
            "uq_contacts_phone_active_per_tenant",
            "tenant_id",
            "phone_e164",
            unique=True,
            postgresql_where="phone_e164 IS NOT NULL AND status = 'active'",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Contact id={self.id} tenant={self.tenant_id} "
            f"name={self.display_name!r} status={self.status!r}>"
        )
