import pytest
import uuid
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def api_client():
    from app.main import create_app
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)

@pytest.fixture(scope="module")
def platform_admin(api_client):
    import os, psycopg
    from app.core.security import hash_password
    dsn = os.environ.get("MIGRATION_DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
    
    admin_id = str(uuid.uuid4())
    password = "AdminPassword123!"
    email = f"admin-{admin_id}@demo.com"
    
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, display_name, password_hash, status, system_role)
            VALUES (%s, %s, %s, %s, 'active', 'platform_admin')
            """,
            (admin_id, email, "Platform Admin", hash_password(password))
        )
        
    response = api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200, response.text
    
    yield email, password, admin_id, response.json()["csrf_token"]
    
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DELETE FROM platform_audit_events WHERE actor_user_id = %s", (admin_id,))
        conn.execute("DELETE FROM users WHERE id = %s", (admin_id,))

@pytest.mark.integration
class TestDay4Endpoints:
    def test_admin_create_tenant(self, api_client, platform_admin):
        _, _, _, csrf = platform_admin
        
        payload = {
            "slug": f"test-tenant-{uuid.uuid4().hex[:6]}",
            "display_name": "Test Tenant",
            "industry_tag": "retail",
            "package_code": "starter"
        }
        
        response = api_client.post(
            "/api/v1/admin/tenants",
            json=payload,
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf}
        )
        assert response.status_code == 201
        data = response.json()
        assert "tenant_id" in data
        
    def test_get_packages(self, api_client, platform_admin):
        _, _, _, csrf = platform_admin
        response = api_client.get(
            "/api/v1/packages",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf}
        )
        assert response.status_code == 200
        packages = response.json()
        assert len(packages) == 10
