from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenants import Tenant, TenantMembership
from app.db.session import get_db_session
from app.modules.auth.dependencies import require_csrf
from app.modules.plans import service
from app.modules.plans.schemas import PackageDTO, SubscriptionDetailDTO
from app.modules.tenancy.dependencies import require_role

router = APIRouter()

from typing import Any


@router.get("/packages", response_model=dict[str, Any])
async def get_packages_route(
    user_session: tuple = Depends(require_csrf), db: AsyncSession = Depends(get_db_session)
):
    """
    W1-060: GET /api/v1/packages
    Authenticated catalogue, price/limits and planned availability
    """
    items = await service.get_packages(db)
    return {"items": [PackageDTO.model_validate(i) for i in items]}


@router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionDetailDTO)
async def get_tenant_subscription_route(
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(
        require_role(["owner", "manager"])
    ),
    db: AsyncSession = Depends(get_db_session),
):
    """
    W1-061: GET /api/v1/tenants/{tenant_id}/subscription
    Owner/Manager | Package version; trial/status; usage="N/A"
    """
    tenant, membership = tenant_and_membership
    return await service.get_tenant_subscription(db, tenant.id)
