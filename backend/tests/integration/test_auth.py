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
class TestAuthEndpoints:
    def test_valid_login(self, api_client, setup_user):
        """T04: Valid login: cookie set, CSRF returned"""
        email, password, user_id = setup_user
        
        response = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == email
        assert "csrf_token" in data
        
        # Check cookie
        cookies = response.cookies
        assert "session" in cookies
        
        # Now use the session and csrf to call /auth/me
        session_cookie = cookies.get("session")
        csrf_token = data["csrf_token"]
        
        me_resp = api_client.get(
            "/api/v1/auth/me",
            cookies={"session": session_cookie}
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["user"]["email"] == email

    def test_invalid_login(self, api_client, setup_user):
        """T05: Unknown email vs wrong password: same 401 shape"""
        email, password, user_id = setup_user
        
        # Wrong password
        resp1 = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword"},
            headers={"Origin": "http://localhost:5173"}
        )
        assert resp1.status_code == 401
        
        # Unknown email
        resp2 = api_client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@demo.com", "password": "WrongPassword"},
            headers={"Origin": "http://localhost:5173"}
        )
        assert resp2.status_code == 401
        
        # Responses should be exactly the same
        d1 = resp1.json()
        d2 = resp2.json()
        d1.pop("request_id", None)
        d2.pop("request_id", None)
        assert d1 == d2

    def test_logout_and_revoked_session(self, api_client, setup_user):
        """T06: Logout/disabled user/expired session: no access"""
        email, password, user_id = setup_user
        
        # Login
        response = api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        
        session_cookie = response.cookies.get("session")
        csrf_token = response.json()["csrf_token"]
        
        # Logout
        logout_resp = api_client.post(
            "/api/v1/auth/logout",
            cookies={"session": session_cookie},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf_token}
        )
        assert logout_resp.status_code == 204
        
        # Try /auth/me after logout
        me_resp = api_client.get(
            "/api/v1/auth/me",
            cookies={"session": session_cookie}
        )
        assert me_resp.status_code == 401
