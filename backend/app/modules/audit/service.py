import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import PlatformAuditEvent, TenantAuditEvent


async def log_platform_event(
    db: AsyncSession,
    actor_user_id: uuid.UUID,
    action: str,
    target_tenant_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = PlatformAuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        target_tenant_id=target_tenant_id,
        target_user_id=target_user_id,
        request_id=request_id,
        metadata=metadata or {},
    )
    db.add(event)


async def log_tenant_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = TenantAuditEvent(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        metadata=metadata or {},
    )
    db.add(event)
