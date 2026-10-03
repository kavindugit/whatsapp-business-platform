from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import clear_session_cookie_kwargs, session_cookie_kwargs
from app.db.models.users import AuthSession, User
from app.db.session import get_db_session
from app.modules.auth.dependencies import (
    get_current_session,
    get_redis,
    require_csrf,
    require_origin,
)
from app.modules.auth.schemas import AuthResponse, LoginRequest, MeResponse
from app.modules.auth.service import (
    authenticate_user,
    create_session_for_user,
    get_user_memberships,
    get_user_summary,
    revoke_session,
)
from app.modules.auth.throttle import check_login_throttle, clear_login_throttle

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(require_origin)])
async def login(
    request: Request,
    response: Response,
    creds: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
    redis_client: Redis[Any] = Depends(get_redis),
) -> AuthResponse:
    ip_address = request.client.host if request.client else "127.0.0.1"

    # 1. Throttle check
    await check_login_throttle(redis_client, creds.email, ip_address)

    # 2. Authenticate
    user = await authenticate_user(db, creds)

    # 3. Success, clear throttle
    await clear_login_throttle(redis_client, creds.email)

    # 4. Create Session
    raw_token, csrf_token = await create_session_for_user(db, str(user.id))

    # 5. Set Cookie
    settings = get_settings()
    cookie_kwargs = session_cookie_kwargs(
        cookie_name=settings.session_cookie_name,
        value=raw_token,
        max_age_seconds=settings.session_idle_minutes * 60,
        is_production=settings.is_production,
    )
    response.set_cookie(**cookie_kwargs)  # type: ignore[arg-type]

    user_summary = await get_user_summary(user)
    memberships = await get_user_memberships(db, str(user.id))
    return AuthResponse(user=user_summary, csrf_token=csrf_token, memberships=memberships)


@router.post("/logout", status_code=204, dependencies=[Depends(require_origin)])
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    user_session: tuple[User, AuthSession] = Depends(require_csrf),
) -> None:
    _, auth_session = user_session

    # 1. Revoke in DB
    await revoke_session(db, auth_session.token_hash)

    # 2. Clear cookie
    settings = get_settings()
    cookie_kwargs = clear_session_cookie_kwargs(
        cookie_name=settings.session_cookie_name, is_production=settings.is_production
    )
    response.set_cookie(**cookie_kwargs)  # type: ignore[arg-type]


@router.get("/me", response_model=MeResponse)
async def get_me(
    user_session: tuple[User, AuthSession] = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    user, auth_session = user_session
    user_summary = await get_user_summary(user)
    memberships = await get_user_memberships(db, str(user.id))
    return MeResponse(
        user=user_summary, csrf_token=auth_session.csrf_token, memberships=memberships
    )
