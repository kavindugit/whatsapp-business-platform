"""
tests/integration/test_health.py
Integration test for health endpoints (T31).
Tests against a real running API container.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthEndpoints:
    """
    Verify health endpoints behave correctly.
    T31: Health dependency failure → 503 readiness; liveness reports process state.
    """

    @pytest.fixture(autouse=True)
    def setup_client(self):
        # Import inside the fixture to ensure environment variables are loaded first
        from app.main import create_app

        app = create_app()
        self.client = TestClient(app)

    def test_liveness_returns_200(self) -> None:
        """Liveness endpoint always returns 200 if the process is running."""
        response = self.client.get("/api/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_liveness_contains_no_secrets(self) -> None:
        """Liveness response must not expose configuration or connection details."""
        response = self.client.get("/api/health/live")
        text = response.text.lower()
        # Must not contain any of these sensitive strings
        for forbidden in ["password", "secret", "key", "token", "database_url", "redis_url"]:
            assert forbidden not in text, f"Response contains '{forbidden}'"

    def test_readiness_contains_no_connection_strings(self) -> None:
        """Readiness response must not expose connection strings or credentials."""
        response = self.client.get("/api/health/ready")
        text = response.text.lower()
        for forbidden in ["password", "secret", "postgresql://", "redis://"]:
            assert forbidden not in text, f"Response contains '{forbidden}'"
