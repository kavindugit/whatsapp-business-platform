"""
app/db/models/settings.py
Tenant-owned model: BusinessSettings.
Protected by PostgreSQL Row-Level Security.
RLS policy: tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BusinessSettings(Base):
    __tablename__ = "business_settings"

    # Primary key is also the FK to tenants — one row per tenant
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    business_name: Mapped[str] = mapped_column(String(120), nullable=False)
    public_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    public_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    time_zone: Mapped[str] = mapped_column(String(60), nullable=False, default="Asia/Colombo")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="LKR")
    reply_language: Mapped[str] = mapped_column(String(10), nullable=False, default="auto")
    # Seven-day opening hours: {"mon": [{start, end}, ...], "tue": [...], ...}
    opening_hours: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    escalation_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="settings")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<BusinessSettings tenant={self.tenant_id} name={self.business_name!r}>"
