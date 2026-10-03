import uuid
import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.core.clock import system_clock
from app.core.errors import NotFoundError, ConflictError
from app.db.models.tenants import Tenant, TenantMembership
from app.db.models.users import User
from app.db.models.plans import Subscription, PackageVersion
from app.db.models.settings import BusinessSettings
from app.db.tenant_context import provisioning_transaction, tenant_transaction
from app.modules.audit.service import log_platform_event, log_tenant_event
from app.modules.tenancy.schemas import TenantCreate, TenantStatusUpdate, BusinessSettingsUpdate

import json
from app.db.models.audit import PlatformAuditEvent

async def create_tenant(
    db: AsyncSession,
    actor_user: User,
    payload: TenantCreate
) -> uuid.UUID:
    new_tenant_id = uuid.uuid4()
    now = system_clock.utcnow()

    conn = await db.connection()
    
    engine = db.bind
    async with engine.connect() as conn:
        async with provisioning_transaction(conn, new_tenant_id) as txn:
            # Create Tenant
            await txn.execute(
                Tenant.__table__.insert().values(
                    id=new_tenant_id,
                    slug=payload.slug,
                    display_name=payload.display_name,
                    legal_name=payload.legal_name,
                    industry_tag=payload.industry_tag,
                    status="active",
                    version=1,
                    created_at=now,
                    updated_at=now
                )
            )

            # Get package version
            pv_res = await txn.execute(
                select(PackageVersion.id).where(
                    PackageVersion.package_code == payload.package_code,
                    PackageVersion.version == 1
                )
            )
            pv_id = pv_res.scalar_one_or_none()
            if not pv_id:
                raise NotFoundError("Package version not found.")

            # Create Subscription
            await txn.execute(
                Subscription.__table__.insert().values(
                    id=uuid.uuid4(),
                    tenant_id=new_tenant_id,
                    package_version_id=pv_id,
                    status="trial",
                    period_start=now,
                    period_end=now + datetime.timedelta(days=14),
                    anchor_day=now.day,
                    created_at=now,
                    updated_at=now
                )
            )

            # Provision Owner if requested
            if payload.owner_email:
                owner_res = await txn.execute(
                    select(User.id).where(User.email == payload.owner_email)
                )
                owner_id = owner_res.scalar_one_or_none()
                if not owner_id:
                    # Create the owner user if password provided
                    if payload.owner_password:
                        from app.core.security import hash_password
                        new_owner_id = uuid.uuid4()
                        await txn.execute(
                            User.__table__.insert().values(
                                id=new_owner_id,
                                email=payload.owner_email,
                                display_name=payload.owner_display_name or payload.owner_email,
                                password_hash=hash_password(payload.owner_password),
                                status="active",
                                system_role=None,
                                created_at=now,
                                updated_at=now,
                            )
                        )
                        owner_id = new_owner_id
                    else:
                        raise NotFoundError("Owner email not found. Provide owner_password to create the user.")

                await txn.execute(
                    TenantMembership.__table__.insert().values(
                        id=uuid.uuid4(),
                        tenant_id=new_tenant_id,
                        user_id=owner_id,
                        role="owner",
                        status="active",
                        created_at=now,
                        updated_at=now
                    )
                )
            
            # Create BusinessSettings (Tenant-owned)
            await txn.execute(
                BusinessSettings.__table__.insert().values(
                    tenant_id=new_tenant_id,
                    business_name=payload.display_name,
                    time_zone="Asia/Colombo",
                    currency="LKR",
                    reply_language="auto",
                    opening_hours={},
                    version=1,
                    created_at=now,
                    updated_at=now
                )
            )

            # Audit
            await txn.execute(
                PlatformAuditEvent.__table__.insert().values(
                    id=uuid.uuid4(),
                    actor_user_id=actor_user.id,
                    action="create_tenant",
                    target_tenant_id=new_tenant_id,
                    metadata=json.dumps({"slug": payload.slug, "package": payload.package_code}),
                    created_at=now
                )
            )

    return new_tenant_id

async def get_tenants_admin(db: AsyncSession, limit: int = 25, offset: int = 0) -> List[Tenant]:
    stmt = select(Tenant).order_by(Tenant.created_at.desc(), Tenant.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def count_tenants_admin(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Tenant.id)))
    return result.scalar_one() or 0

async def get_tenant_admin(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise NotFoundError("Workspace not found.")
    return tenant

async def update_tenant_status_admin(
    db: AsyncSession,
    actor_user: User,
    tenant_id: uuid.UUID,
    payload: TenantStatusUpdate
) -> Tenant:
    tenant = await get_tenant_admin(db, tenant_id)
    if tenant.version != payload.expected_version:
        raise ConflictError("This record changed. Refresh and try again.")
    
    tenant.status = payload.status
    tenant.version += 1
    tenant.updated_at = system_clock.utcnow()
    
    await log_platform_event(
        db=db,
        actor_user_id=actor_user.id,
        action=f"update_tenant_status_to_{payload.status}",
        target_tenant_id=tenant_id,
        metadata={"reason": payload.reason, "version": tenant.version}
    )
    
    await db.commit()
    await db.refresh(tenant)
    return tenant

async def get_tenant_settings(db: AsyncSession, tenant_id: uuid.UUID) -> BusinessSettings:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        result = await txn.execute(select(BusinessSettings).where(BusinessSettings.tenant_id == tenant_id))
        row = result.scalar_one_or_none()
        if not row:
            raise NotFoundError("Settings not found.")
        return row

async def update_tenant_settings(
    db: AsyncSession,
    actor_user: User,
    tenant_id: uuid.UUID,
    payload: BusinessSettingsUpdate
) -> BusinessSettings:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        res = await txn.execute(select(BusinessSettings).where(BusinessSettings.tenant_id == tenant_id))
        settings = res.scalar_one_or_none()
        if not settings:
            raise NotFoundError("Settings not found.")
        
        if settings.version != payload.expected_version:
            raise ConflictError("This record changed. Refresh and try again.")
            
        now = system_clock.utcnow()
        
        # We update via core since we are in tenant_transaction and using txn
        await txn.execute(
            BusinessSettings.__table__.update()
            .where(BusinessSettings.tenant_id == tenant_id)
            .values(
                business_name=payload.business_name,
                public_email=payload.public_email,
                public_phone=payload.public_phone,
                address_text=payload.address_text,
                time_zone=payload.time_zone,
                currency=payload.currency,
                reply_language=payload.reply_language,
                opening_hours=payload.opening_hours,
                escalation_text=payload.escalation_text,
                version=settings.version + 1,
                updated_at=now
            )
        )
        
        # log_tenant_event must use txn too
        import json
        from app.db.models.audit import TenantAuditEvent
        await txn.execute(
            TenantAuditEvent.__table__.insert().values(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor_user.id,
                action="update_settings",
                metadata=json.dumps({"version": settings.version + 1}),
                created_at=now
            )
        )

    # After txn ends, return the new settings
    async with tenant_transaction(await db.connection(), tenant_id) as txn:
        result = await txn.execute(select(BusinessSettings).where(BusinessSettings.tenant_id == tenant_id))
        return result.scalar_one()

async def get_tenant_members(db: AsyncSession, tenant_id: uuid.UUID) -> List[dict]:
    # Since members is a control-plane table, we can just query it with db
    stmt = (
        select(TenantMembership, User)
        .join(User, User.id == TenantMembership.user_id)
        .where(TenantMembership.tenant_id == tenant_id)
        .order_by(TenantMembership.created_at)
    )
    result = await db.execute(stmt)
    members = []
    for membership, user in result:
        members.append({
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": membership.role,
            "status": membership.status,
            "created_at": membership.created_at
        })
    return members

