import os
import uuid
import pytest
import psycopg
from fastapi.testclient import TestClient

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
    return TestClient(app)

@pytest.mark.integration
class TestCSRF:
    def test_missing_origin(self, api_client, setup_user):
        """T08: Missing Origin on mutation (login) -> 403 Forbidden"""
        email, password, _ = setup_user
        
        # Missing Origin header entirely
        response = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 403
        
        # Invalid Origin header
        response = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers={"Origin": "http://evil.com"}
        )
        assert response.status_code == 403

    def test_missing_or_invalid_csrf(self, api_client, setup_user):
        """T08: Missing or invalid CSRF token on mutation (logout) -> 401/403"""
        email, password, _ = setup_user
        
        # Login successfully first
        response = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers={"Origin": "http://localhost:5173"}
        )
        session_cookie = response.cookies.get("session")
        
        # Logout with missing CSRF
        logout_no_csrf = api_client.post(
            "/api/v1/auth/logout",
            cookies={"session": session_cookie},
            headers={"Origin": "http://localhost:5173"}
        )
        assert logout_no_csrf.status_code == 401
        
        # Logout with invalid CSRF
        logout_bad_csrf = api_client.post(
            "/api/v1/auth/logout",
            cookies={"session": session_cookie},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "bad_token"}
        )
        assert logout_bad_csrf.status_code == 403
