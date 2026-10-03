import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenants import Tenant, TenantMembership
from app.db.session import get_db_session
from app.modules.auth.dependencies import require_csrf
from app.modules.contacts import service
from app.modules.contacts.schemas import ContactAction, ContactCreate, ContactDTO, ContactUpdate
from app.modules.tenancy.dependencies import require_membership, require_role

router = APIRouter()


@router.get("/tenants/{tenant_id}/contacts", response_model=dict[str, Any])
async def list_contacts_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(require_membership),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    offset = (page - 1) * page_size
    items = await service.get_contacts(db, tenant.id, page_size, offset, search, status_filter)
    total = await service.count_contacts(db, tenant.id, search, status_filter)
    items_dto = [ContactDTO.model_validate(c) for c in items]
    return {"items": items_dto, "total": total, "page": page, "page_size": page_size}


@router.post(
    "/tenants/{tenant_id}/contacts", status_code=status.HTTP_201_CREATED, response_model=ContactDTO
)
async def create_contact_route(
    payload: ContactCreate,
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(require_membership),
    user_session: tuple = Depends(require_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    actor_user, _ = user_session
    return await service.create_contact(db, actor_user, tenant.id, payload)


@router.get("/tenants/{tenant_id}/contacts/{contact_id}", response_model=ContactDTO)
async def get_contact_route(
    contact_id: uuid.UUID,
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(require_membership),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    return await service.get_contact(db, tenant.id, contact_id)


@router.patch("/tenants/{tenant_id}/contacts/{contact_id}", response_model=ContactDTO)
async def update_contact_route(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(require_membership),
    user_session: tuple = Depends(require_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    actor_user, _ = user_session
    return await service.update_contact(db, actor_user, tenant.id, contact_id, payload)


@router.post("/tenants/{tenant_id}/contacts/{contact_id}/archive", response_model=ContactDTO)
async def archive_contact_route(
    contact_id: uuid.UUID,
    payload: ContactAction,
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(
        require_role(["owner", "manager"])
    ),
    user_session: tuple = Depends(require_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    actor_user, _ = user_session
    return await service.archive_contact(
        db, actor_user, tenant.id, contact_id, payload.expected_version
    )


@router.post("/tenants/{tenant_id}/contacts/{contact_id}/restore", response_model=ContactDTO)
async def restore_contact_route(
    contact_id: uuid.UUID,
    payload: ContactAction,
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(
        require_role(["owner", "manager"])
    ),
    user_session: tuple = Depends(require_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    tenant, membership = tenant_and_membership
    actor_user, _ = user_session
    return await service.restore_contact(
        db, actor_user, tenant.id, contact_id, payload.expected_version
    )
