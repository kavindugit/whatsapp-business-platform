import datetime
from unittest.mock import patch
import pytest

from app.core.errors import UnauthorizedError
from app.db.models.users import User, AuthSession
from app.modules.auth.dependencies import get_current_session
from app.core.config import get_settings
from app.core.security import hash_session_token
from app.core.clock import FixedClock

class DummyRequest:
    method = "GET"
    headers = {}

class DummySession:
    async def execute(self, stmt):
        class Result:
            def scalar_one_or_none(self):
                user = User(
                    id="00000000-0000-0000-0000-000000000000",
                    email="test@demo.local",
                    status="active"
                )
                auth = AuthSession(
                    id="11111111-1111-1111-1111-111111111111",
                    token_hash=hash_session_token("valid_token"),
                    csrf_token="csrf",
                    created_at=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
                    last_seen_at=datetime.datetime(2025, 1, 1, 2, 0, tzinfo=datetime.timezone.utc),
                    absolute_expiry=datetime.datetime(2025, 1, 1, 12, 0, tzinfo=datetime.timezone.utc),
                    user=user,
                    revoked_at=None
                )
                return auth
        return Result()
    
    async def commit(self):
        pass

@pytest.mark.asyncio
async def test_session_idle_expiry():
    """T07: Idle expiry with injected clock."""
    req = DummyRequest()
    db = DummySession()
    
    valid_time = datetime.datetime(2025, 1, 1, 2, 15, tzinfo=datetime.timezone.utc)
    mock_clock = FixedClock(valid_time)
    with patch("app.modules.auth.dependencies.system_clock", mock_clock):
        user, auth = await get_current_session(request=req, session="valid_token", db=db)
        assert auth.last_seen_at == valid_time
        
    expired_time = datetime.datetime(2025, 1, 1, 2, 35, tzinfo=datetime.timezone.utc)
    mock_clock = FixedClock(expired_time)
    with patch("app.modules.auth.dependencies.system_clock", mock_clock):
        with pytest.raises(UnauthorizedError, match="Session has expired"):
            await get_current_session(request=req, session="valid_token", db=db)

@pytest.mark.asyncio
async def test_session_absolute_expiry():
    """T07: Absolute expiry with injected clock."""
    req = DummyRequest()
    db = DummySession()
    
    expired_time = datetime.datetime(2025, 1, 1, 12, 5, tzinfo=datetime.timezone.utc)
    mock_clock = FixedClock(expired_time)
    with patch("app.modules.auth.dependencies.system_clock", mock_clock):
        with pytest.raises(UnauthorizedError, match="Session has expired"):
            await get_current_session(request=req, session="valid_token", db=db)
