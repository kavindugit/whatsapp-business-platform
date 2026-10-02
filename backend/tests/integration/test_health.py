"""
tests/integration/test_health.py
Integration test for health endpoints (T31).
Tests against a real running API container.
"""
from __future__ import annotations

import pytest
import httpx


@pytest.mark.integration
class TestHealthEndpoints:
    """
    Verify health endpoints behave correctly.
    T31: Health dependency failure → 503 readiness; liveness reports process state.
    """

    BASE_URL = "http://localhost:8000"  # Direct API access in tests

    def test_liveness_returns_200(self) -> None:
        """Liveness endpoint always returns 200 if the process is running."""
        with httpx.Client(base_url=self.BASE_URL) as client:
            response = client.get("/api/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_liveness_contains_no_secrets(self) -> None:
        """Liveness response must not expose configuration or connection details."""
        with httpx.Client(base_url=self.BASE_URL) as client:
            response = client.get("/api/health/live")
        text = response.text.lower()
        # Must not contain any of these sensitive strings
        for forbidden in ["password", "secret", "key", "token", "database_url", "redis_url"]:
            assert forbidden not in text, f"Response contains '{forbidden}'"

    def test_readiness_contains_no_connection_strings(self) -> None:
        """Readiness response must not expose connection strings or credentials."""
        with httpx.Client(base_url=self.BASE_URL) as client:
            response = client.get("/api/health/ready")
        text = response.text.lower()
        for forbidden in ["password", "secret", "postgresql://", "redis://"]:
            assert forbidden not in text, f"Response contains '{forbidden}'"
