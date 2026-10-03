"""
tests/conftest.py
Pytest configuration and shared fixtures.

Day 1: Minimal fixtures — database-backed fixtures added in Day 2.
"""
from __future__ import annotations

import os

import pytest
import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ensure we never accidentally run tests against the production/dev database
def pytest_configure(config: pytest.Config) -> None:
    """Validate test environment before any tests run."""
    test_db = os.environ.get("TEST_DATABASE_URL", "")
    prod_db = os.environ.get("DATABASE_URL", "")

    # Refuse to run if TEST_DATABASE_URL points to the production DB
    if test_db and prod_db and test_db == prod_db:
        raise RuntimeError(
            "TEST_DATABASE_URL must be different from DATABASE_URL. "
            "Tests are NOT safe to run against the development or production database."
        )

    # Override DATABASE_URL so the FastAPI app uses the test database
    if test_db:
        os.environ["DATABASE_URL"] = test_db

    app_env = os.environ.get("APP_ENV", "")
    if app_env == "production":
        raise RuntimeError(
            "Tests cannot run with APP_ENV=production. "
            "Set APP_ENV=test in your test environment."
        )
