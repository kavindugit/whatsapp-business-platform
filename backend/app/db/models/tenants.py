"""
app/db/models/tenants.py
Control-plane models: Tenant and TenantMembership.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    industry_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    memberships: Mapped[list[TenantMembership]] = relationship(
        "TenantMembership", back_populates="tenant", cascade="all, delete-orphan"
    )
    subscription: Mapped[Subscription | None] = relationship(  # type: ignore[name-defined]
        "Subscription", back_populates="tenant", uselist=False
    )
    settings: Mapped[BusinessSettings | None] = relationship(  # type: ignore[name-defined]
        "BusinessSettings", back_populates="tenant", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r} status={self.status!r}>"


class TenantMembership(Base):
    __tablename__ = "tenant_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="memberships")
    user: Mapped[User] = relationship("User", back_populates="memberships")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
        # Partial unique index for at-most-one active owner per tenant
        # (defined in migration with WHERE clause — SQLAlchemy doesn't support partial unique indexes inline)
        Index("ix_tenant_memberships_tenant_id", "tenant_id"),
        Index("ix_tenant_memberships_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TenantMembership tenant={self.tenant_id} user={self.user_id} "
            f"role={self.role!r} status={self.status!r}>"
        )
