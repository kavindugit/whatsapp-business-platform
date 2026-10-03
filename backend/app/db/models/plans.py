"""
app/db/models/plans.py
Control-plane models: Package, PackageVersion, Subscription.

Key invariants (W1-060, W1-061):
- package_versions is IMMUTABLE after creation (no UPDATE/DELETE granted to app_runtime)
- subscriptions snapshot the package_version_id at creation time
- Updating a PackageVersion must not silently mutate existing subscriptions
- All prices are in integer minor units (LKR paise: 6900 LKR = 690000 minor units)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Package(Base):
    __tablename__ = "packages"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    release_status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    versions: Mapped[list[PackageVersion]] = relationship(
        "PackageVersion", back_populates="package"
    )

    def __repr__(self) -> str:
        return f"<Package code={self.code!r} status={self.release_status!r}>"


class PackageVersion(Base):
    __tablename__ = "package_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("packages.code"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="LKR")
    monthly_price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # minor units
    setup_price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # minor units
    staff_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    number_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # JSON object: {feature_code: true, ...} — validated against feature registry
    feature_permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # JSON object: {metric_name: int_limit, ...} — explicit 0 means not included, never null
    metric_limits: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    package: Mapped[Package] = relationship("Package", back_populates="versions")
    subscriptions: Mapped[list[Subscription]] = relationship(
        "Subscription", back_populates="package_version"
    )

    __table_args__ = (
        UniqueConstraint("package_code", "version", name="uq_package_versions_code_version"),
    )

    def __repr__(self) -> str:
        return f"<PackageVersion package={self.package_code!r} v={self.version}>"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    package_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("package_versions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="trial")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    anchor_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="subscription")  # type: ignore[name-defined]
    package_version: Mapped[PackageVersion] = relationship(
        "PackageVersion", back_populates="subscriptions"
    )

    def __repr__(self) -> str:
        return f"<Subscription tenant={self.tenant_id} status={self.status!r}>"
