import datetime
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from fastapi import Cookie, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.clock import system_clock
from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import hash_session_token, validate_csrf, validate_origin
from app.db.models.users import AuthSession, User
from app.db.session import get_db_session


async def get_redis() -> AsyncGenerator[aioredis.Redis[Any], None]:
    settings = get_settings()
    client = aioredis.from_url(settings.redis_url)
    try:
        yield client
    finally:
        await client.close()


def require_origin(request: Request) -> None:
    """Dependency that ensures the Origin header is allowed."""
    settings = get_settings()
    # Note: Only require origin on POST/PATCH/DELETE
    if request.method in ("POST", "PATCH", "DELETE"):
        validate_origin(request, settings.parsed_allowed_origins)


async def get_current_session(
    request: Request,
    session: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> tuple[User, AuthSession]:
    """
    Validates the session cookie.
    Returns (User, AuthSession).
    Raises UnauthorizedError if missing or invalid.
    """
    if not session:
        raise UnauthorizedError("Authentication is required.")

    token_hash = hash_session_token(session)
    now = system_clock.utcnow()

    # We must load the AuthSession and its User
    # We can do this with a join or rely on lazy loading if session is configured right?
    # Better to join them to avoid N+1 and async lazy load errors.
    from sqlalchemy.orm import selectinload

    stmt = (
        select(AuthSession)
        .options(selectinload(AuthSession.user))
        .where(AuthSession.token_hash == token_hash)
        .where(AuthSession.revoked_at == None)  # noqa
    )
    result = await db.execute(stmt)
    auth_session = result.scalar_one_or_none()

    if not auth_session:
        raise UnauthorizedError("Invalid or expired session.")

    settings = get_settings()
    idle_expiry = auth_session.last_seen_at + datetime.timedelta(
        minutes=settings.session_idle_minutes
    )

    if now > idle_expiry or now > auth_session.absolute_expiry:
        raise UnauthorizedError("Session has expired.")

    if auth_session.user.status != "active":
        raise UnauthorizedError("Your account has been disabled.")

    # Update last_seen_at
    # To prevent DB write on every single request, we could throttle the update, but for now we just do it.
    auth_session.last_seen_at = now
    await db.commit()

    return auth_session.user, auth_session


async def require_csrf(
    request: Request, user_session: tuple[User, AuthSession] = Depends(get_current_session)
) -> tuple[User, AuthSession]:
    """Dependency that ensures X-CSRF-Token matches the session."""
    user, auth_session = user_session
    if request.method in ("POST", "PATCH", "DELETE"):
        validate_csrf(request, auth_session.csrf_token)
    return user, auth_session
