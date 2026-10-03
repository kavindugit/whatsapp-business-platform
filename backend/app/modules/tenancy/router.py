import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenants import Tenant, TenantMembership
from app.db.models.users import User
from app.db.session import get_db_session
from app.modules.auth.dependencies import require_csrf
from app.modules.tenancy import service
from app.modules.tenancy.dependencies import (
    require_membership,
    require_platform_admin,
    require_role,
)
from app.modules.tenancy.schemas import (
    BusinessSettingsDTO,
    BusinessSettingsUpdate,
    MemberDTO,
    TenantCreate,
    TenantDTO,
    TenantStatusUpdate,
)

router = APIRouter()


# -----------------
# ADMIN ROUTES
# -----------------
@router.get("/admin/tenants", response_model=dict[str, Any])
async def list_tenants_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    admin_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db_session),
):
    offset = (page - 1) * page_size
    items = await service.get_tenants_admin(db, page_size, offset)
    total = await service.count_tenants_admin(db)
    items_dto = [TenantDTO.model_validate(t) for t in items]
    return {"items": items_dto, "total": total, "page": page, "page_size": page_size}


@router.post("/admin/tenants", status_code=status.HTTP_201_CREATED, response_model=dict[str, Any])
async def create_tenant_admin(
    payload: TenantCreate,
    admin_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db_session),
):
    tenant_id = await service.create_tenant(db, admin_user, payload)
    return {"tenant_id": tenant_id}


@router.get("/admin/tenants/{tenant_id}", response_model=TenantDTO)
async def get_tenant_admin_route(
    tenant_id: uuid.UUID,
    admin_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db_session),
):
    return await service.get_tenant_admin(db, tenant_id)


@router.patch("/admin/tenants/{tenant_id}/status", response_model=TenantDTO)
async def update_tenant_status_admin_route(
    tenant_id: uuid.UUID,
    payload: TenantStatusUpdate,
    admin_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db_session),
):
    return await service.update_tenant_status_admin(db, admin_user, tenant_id, payload)


# -----------------
# TENANT ROUTES
# -----------------
@router.get("/tenants/{tenant_id}/settings", response_model=BusinessSettingsDTO)
async def get_settings_route(
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(require_membership),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    return await service.get_tenant_settings(db, tenant.id)


@router.patch("/tenants/{tenant_id}/settings", response_model=BusinessSettingsDTO)
async def update_settings_route(
    payload: BusinessSettingsUpdate,
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(
        require_role(["owner", "manager"])
    ),
    user_session: tuple = Depends(require_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    actor_user, _ = user_session
    return await service.update_tenant_settings(db, actor_user, tenant.id, payload)


@router.get("/tenants/{tenant_id}/members", response_model=dict[str, Any])
async def get_members_route(
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(
        require_role(["owner", "manager"])
    ),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    items = await service.get_tenant_members(db, tenant.id)
    items_dto = [MemberDTO.model_validate(m) for m in items]
    return {"items": items_dto}
