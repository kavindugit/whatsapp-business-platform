"""
app/db/models/audit.py
Audit event models: PlatformAuditEvent and TenantAuditEvent.

Security invariants:
- Both tables are APPEND-ONLY: no UPDATE or DELETE granted to app_runtime
- Metadata field stores only safe identifiers, action names and field names
- Never stores: passwords, session tokens, CSRF values, raw notes, contact exports
- TenantAuditEvent is tenant-scoped and protected by RLS
- PlatformAuditEvent is control-plane and accessed only by operator services
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformAuditEvent(Base):
    """
    Records operator-level actions: tenant creation/suspension, membership changes,
    operator provisioning, and admin access patterns.
    Not protected by tenant RLS — access controlled by application services only.
    """
    __tablename__ = "platform_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Safe metadata only: action names, field names, safe identifiers
    # NEVER: passwords, tokens, raw notes, contact data
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_platform_audit_events_actor", "actor_user_id"),
        Index("ix_platform_audit_events_tenant", "target_tenant_id"),
        Index("ix_platform_audit_events_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PlatformAuditEvent action={self.action!r} actor={self.actor_user_id}>"


class TenantAuditEvent(Base):
    """
    Records tenant-scoped mutations: settings changes, contact CRUD, etc.
    Protected by PostgreSQL Row-Level Security — only visible within the correct tenant context.
    Append-only: app_runtime has no UPDATE or DELETE privilege on this table.
    """
    __tablename__ = "tenant_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_tenant_audit_events_tenant", "tenant_id"),
        Index("ix_tenant_audit_events_tenant_created", "tenant_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TenantAuditEvent tenant={self.tenant_id} action={self.action!r}>"
