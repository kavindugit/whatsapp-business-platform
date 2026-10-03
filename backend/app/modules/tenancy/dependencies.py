import uuid
from collections.abc import Sequence

from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import ForbiddenError
from app.db.models.tenants import Tenant, TenantMembership
from app.db.models.users import AuthSession, User
from app.db.session import get_db_session
from app.modules.auth.dependencies import require_csrf


async def require_platform_admin(
    user_session: tuple[User, AuthSession] = Depends(require_csrf),
) -> User:
    """Requires the user to be a platform_admin."""
    user, _ = user_session
    if user.system_role != "platform_admin":
        raise ForbiddenError("Platform admin access required.")
    return user


async def get_tenant_and_membership(
    tenant_id: uuid.UUID = Path(...),
    user_session: tuple[User, AuthSession] = Depends(require_csrf),
    db: AsyncSession = Depends(get_db_session),
) -> tuple[Tenant, TenantMembership]:
    """
    Validates that the user is an active member of the requested tenant.
    Returns (Tenant, TenantMembership).
    """
    user, _ = user_session

    # Query membership and tenant
    stmt = (
        select(TenantMembership, Tenant)
        .join(Tenant, Tenant.id == TenantMembership.tenant_id)
        .where(TenantMembership.tenant_id == tenant_id)
        .where(TenantMembership.user_id == user.id)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        # Non-member tenant request: generic 403 (or 404 for foreign object, but per W1-051:
        # "Non-member tenant request: generic 403")
        raise ForbiddenError("Access to this workspace is denied.")

    membership, tenant = row

    if membership.status != "active":
        raise ForbiddenError("Your membership in this workspace is inactive.")

    return tenant, membership


async def require_membership(
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(get_tenant_and_membership),
) -> tuple[Tenant, TenantMembership]:
    return tenant_and_membership


async def check_suspension(
    tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(get_tenant_and_membership),
) -> tuple[Tenant, TenantMembership]:
    tenant, membership = tenant_and_membership
    if tenant.status == "suspended":
        raise ForbiddenError("This workspace has been suspended.")
    return tenant, membership


def require_role(roles: Sequence[str]):
    async def role_checker(
        tenant_and_membership: tuple[Tenant, TenantMembership] = Depends(check_suspension),
    ) -> tuple[Tenant, TenantMembership]:
        tenant, membership = tenant_and_membership
        if membership.role not in roles:
            raise ForbiddenError(f"Requires one of roles: {', '.join(roles)}")
        return tenant, membership

    return role_checker
