import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.core.config import get_settings
from app.core.clock import system_clock
from app.core.errors import UnauthorizedError
from app.core.security import (
    verify_password,
    dummy_password_check,
    generate_session_token,
    hash_session_token,
    generate_csrf_token
)
from app.db.models.users import User, AuthSession
from app.db.models.tenants import Tenant, TenantMembership
from app.modules.auth.schemas import LoginRequest, UserSummary, MembershipSummary


async def authenticate_user(session: AsyncSession, creds: LoginRequest) -> User:
    """Verifies credentials. Raises UnauthorizedError on failure."""
    stmt = select(User).where(User.email == creds.email.lower())
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        dummy_password_check(creds.password)
        raise UnauthorizedError("Invalid email or password.")

    if not verify_password(creds.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password.")

    if user.status != "active":
        raise UnauthorizedError("Your account has been disabled.")

    return user

async def create_session_for_user(
    db: AsyncSession, user_id: str
) -> tuple[str, str]:
    """
    Creates a new AuthSession.
    Returns (raw_session_token, csrf_token).
    """
    settings = get_settings()
    now = system_clock.utcnow()
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    csrf_token = generate_csrf_token()

    expiry = now + datetime.timedelta(hours=settings.session_absolute_hours)

    auth_session = AuthSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token=csrf_token,
        created_at=now,
        last_seen_at=now,
        absolute_expiry=expiry
    )
    db.add(auth_session)
    await db.commit()
    return raw_token, csrf_token

async def get_user_summary(user: User) -> UserSummary:
    return UserSummary(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        system_role=user.system_role
    )

async def get_user_memberships(db: AsyncSession, user_id: str) -> list[MembershipSummary]:
    """Returns all active workspace memberships for a user, with tenant display names."""
    import uuid
    stmt = (
        select(TenantMembership, Tenant)
        .join(Tenant, Tenant.id == TenantMembership.tenant_id)
        .where(TenantMembership.user_id == uuid.UUID(user_id))
        .where(TenantMembership.status == "active")
        .order_by(TenantMembership.created_at)
    )
    result = await db.execute(stmt)
    memberships = []
    for membership, tenant in result:
        memberships.append(MembershipSummary(
            tenant_id=membership.tenant_id,
            display_name=tenant.display_name,
            role=membership.role,
            status=membership.status,
            created_at=membership.created_at,
        ))
    return memberships

async def revoke_session(db: AsyncSession, token_hash: str) -> None:
    now = system_clock.utcnow()
    stmt = (
        update(AuthSession)
        .where(AuthSession.token_hash == token_hash)
        .where(AuthSession.revoked_at == None) # noqa
        .values(revoked_at=now)
    )
    await db.execute(stmt)
    await db.commit()
