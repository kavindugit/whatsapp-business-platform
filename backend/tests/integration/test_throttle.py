import os
import uuid
import pytest
import psycopg
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.security import hash_password

def get_migration_dsn() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL", "")
    return url.replace("postgresql+psycopg://", "postgresql://")

@pytest.fixture(scope="module")
def setup_user():
    dsn = get_migration_dsn()
    user_id = str(uuid.uuid4())
    password = "MySecurePassword123"
    email = f"test-{user_id}@demo.com"
    
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, display_name, password_hash, status, system_role)
            VALUES (%s, %s, %s, %s, 'active', 'platform_admin')
            """,
            (user_id, email, "Test User", hash_password(password))
        )
    yield email, password, user_id
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DELETE FROM users WHERE id = %s", (user_id,))

@pytest.fixture(scope="module")
def api_client():
    from app.main import create_app
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)

@pytest.mark.integration
class TestThrottle:
    @pytest.mark.asyncio
    async def test_login_throttle_email(self, api_client, setup_user):
        """T09: Login failure thresholds"""
        email, password, _ = setup_user
        
        import redis.asyncio as aioredis
        from app.core.config import get_settings
        settings = get_settings()
        redis = aioredis.from_url(settings.redis_url)
        await redis.flushdb()
        await redis.aclose()

        # Max email attempts is 5. We fail 5 times.
        for _ in range(5):
            response = api_client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword"},
                headers={"Origin": "http://localhost:5173"}
            )
            assert response.status_code == 401
            
        # The 6th time should hit 429
        response = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword"},
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 429
        
    def test_redis_unavailable(self, api_client, setup_user):
        """T09: Redis unavailable -> 503"""
        email, password, _ = setup_user
        
        # Patch check_login_throttle to simulate Redis being down
        with patch("app.modules.auth.router.check_login_throttle") as mock_throttle:
            from app.core.errors import ServiceUnavailableError
            mock_throttle.side_effect = ServiceUnavailableError("Redis is unavailable for throttling")
            
            response = api_client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
                headers={"Origin": "http://localhost:5173"}
            )
            assert response.status_code == 503
