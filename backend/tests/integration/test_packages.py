"""
tests/integration/test_packages.py
T15, T16 — Package catalogue and immutability tests.

T15: All 10 packages present with correct codes, prices, and feature flags.
T16: app_runtime cannot INSERT, UPDATE or DELETE package_versions (immutable).
"""
from __future__ import annotations

import os
import uuid

import pytest
import psycopg


def get_runtime_dsn() -> str:
    url = os.environ.get("TEST_DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not url:
        pytest.skip("TEST_DATABASE_URL not set — skipping package integration tests")
    return url.replace("postgresql+psycopg://", "").replace("postgresql+psycopg2://", "")


# Expected package catalogue (W1-060)
EXPECTED_PACKAGES = {
    "starter":           {"monthly": 690000,   "setup": 2000000,   "staff": 1, "numbers": 1},
    "updates":           {"monthly": 990000,   "setup": 3500000,   "staff": 2, "numbers": 1},
    "receptionist":      {"monthly": 1290000,  "setup": 4000000,   "staff": 2, "numbers": 1},
    "order_desk":        {"monthly": 1990000,  "setup": 6500000,   "staff": 3, "numbers": 1},
    "appointments":      {"monthly": 1990000,  "setup": 6500000,   "staff": 3, "numbers": 1},
    "sales_leads":       {"monthly": 2490000,  "setup": 8500000,   "staff": 4, "numbers": 1},
    "support_team":      {"monthly": 3490000,  "setup": 10000000,  "staff": 5, "numbers": 1},
    "connected_commerce":{"monthly": 4990000,  "setup": 15000000,  "staff": 5, "numbers": 1},
    "retention":         {"monthly": 4490000,  "setup": 10000000,  "staff": 5, "numbers": 1},
    "enterprise":        {"monthly": 14990000, "setup": 60000000,  "staff": 20,"numbers": 3},
}


@pytest.fixture(scope="module")
def runtime_conn():
    dsn = get_runtime_dsn()
    conn = psycopg.connect(dsn, autocommit=False)
    yield conn
    conn.rollback()
    conn.close()


@pytest.mark.integration
class TestT15PackageCatalogue:
    """T15: All 10 packages exist with correct prices and all have release_status='planned'."""

    def test_all_ten_packages_present(self, runtime_conn):
        rows = runtime_conn.execute(
            "SELECT code FROM packages ORDER BY code"
        ).fetchall()
        codes = {row[0] for row in rows}

        missing = set(EXPECTED_PACKAGES.keys()) - codes
        assert not missing, f"T15 FAILED: Missing packages: {missing}"

        assert len(codes) == 10, f"T15 FAILED: Expected 10 packages, got {len(codes)}"

    def test_all_packages_have_planned_status(self, runtime_conn):
        rows = runtime_conn.execute(
            "SELECT code, release_status FROM packages"
        ).fetchall()
        non_planned = [(row[0], row[1]) for row in rows if row[1] != "planned"]
        assert not non_planned, (
            f"T15 FAILED: Packages with non-planned status: {non_planned}. "
            "All packages must be 'planned' in Week 1."
        )

    def test_each_package_has_version_1(self, runtime_conn):
        rows = runtime_conn.execute(
            "SELECT package_code, version FROM package_versions WHERE version = 1"
        ).fetchall()
        versioned_codes = {row[0] for row in rows}

        missing = set(EXPECTED_PACKAGES.keys()) - versioned_codes
        assert not missing, f"T15 FAILED: Packages missing version 1: {missing}"

    def test_prices_correct_in_minor_units(self, runtime_conn):
        rows = runtime_conn.execute(
            "SELECT package_code, monthly_price, setup_price, staff_limit, number_limit "
            "FROM package_versions WHERE version = 1"
        ).fetchall()

        price_map = {row[0]: row for row in rows}

        for code, expected in EXPECTED_PACKAGES.items():
            assert code in price_map, f"T15 FAILED: No version 1 for package {code!r}"
            row = price_map[code]
            assert row[1] == expected["monthly"], (
                f"T15 FAILED: {code} monthly_price = {row[1]}, expected {expected['monthly']}"
            )
            assert row[2] == expected["setup"], (
                f"T15 FAILED: {code} setup_price = {row[2]}, expected {expected['setup']}"
            )
            assert row[3] == expected["staff"], (
                f"T15 FAILED: {code} staff_limit = {row[3]}, expected {expected['staff']}"
            )
            assert row[4] == expected["numbers"], (
                f"T15 FAILED: {code} number_limit = {row[4]}, expected {expected['numbers']}"
            )

    def test_enterprise_has_all_features(self, runtime_conn):
        row = runtime_conn.execute(
            "SELECT feature_permissions FROM package_versions "
            "WHERE package_code = 'enterprise' AND version = 1"
        ).fetchone()

        assert row is not None, "T15 FAILED: enterprise package_version not found"
        features = row[0]  # dict from JSONB

        required = [
            "core_inbox", "contact_directory", "business_settings",
            "ai_answers", "knowledge_base", "catalogue",
            "order_capture", "calendar_booking",
        ]
        for feat in required:
            assert features.get(feat) is True, (
                f"T15 FAILED: enterprise package missing feature {feat!r}"
            )

    def test_starter_excluded_from_ai_features(self, runtime_conn):
        row = runtime_conn.execute(
            "SELECT feature_permissions FROM package_versions "
            "WHERE package_code = 'starter' AND version = 1"
        ).fetchone()

        assert row is not None
        features = row[0]

        assert features.get("ai_answers") is not True, (
            "T15 FAILED: starter package should NOT have ai_answers feature"
        )
        assert features.get("core_inbox") is True, (
            "T15 FAILED: starter package must have core_inbox feature"
        )


@pytest.mark.integration
class TestT16PackageVersionImmutability:
    """
    T16: app_runtime role cannot INSERT, UPDATE, or DELETE from package_versions.
    This enforces the immutability invariant — package versions are only added via migrations.
    """

    def test_runtime_cannot_insert_package_version(self, runtime_conn):
        """app_runtime should not be able to INSERT into package_versions."""
        with pytest.raises(Exception) as exc_info:
            runtime_conn.execute(
                """
                INSERT INTO package_versions
                    (package_code, version, monthly_price, setup_price,
                     staff_limit, number_limit)
                VALUES ('starter', 99, 100000, 200000, 1, 1)
                """
            )
            runtime_conn.commit()

        runtime_conn.rollback()
        error_msg = str(exc_info.value).lower()
        assert any(
            phrase in error_msg
            for phrase in ["permission denied", "privilege", "denied"]
        ), f"T16 FAILED: Expected permission error on INSERT, got: {exc_info.value}"

    def test_runtime_cannot_update_package_version(self, runtime_conn):
        """app_runtime should not be able to UPDATE package_versions."""
        with pytest.raises(Exception) as exc_info:
            runtime_conn.execute(
                "UPDATE package_versions SET monthly_price = 1 WHERE package_code = 'starter'"
            )
            runtime_conn.commit()

        runtime_conn.rollback()
        error_msg = str(exc_info.value).lower()
        assert any(
            phrase in error_msg
            for phrase in ["permission denied", "privilege", "denied"]
        ), f"T16 FAILED: Expected permission error on UPDATE, got: {exc_info.value}"

    def test_runtime_cannot_delete_package_version(self, runtime_conn):
        """app_runtime should not be able to DELETE from package_versions."""
        with pytest.raises(Exception) as exc_info:
            runtime_conn.execute(
                "DELETE FROM package_versions WHERE package_code = 'starter'"
            )
            runtime_conn.commit()

        runtime_conn.rollback()
        error_msg = str(exc_info.value).lower()
        assert any(
            phrase in error_msg
            for phrase in ["permission denied", "privilege", "denied"]
        ), f"T16 FAILED: Expected permission error on DELETE, got: {exc_info.value}"

    def test_runtime_cannot_insert_new_package(self, runtime_conn):
        """app_runtime should not be able to INSERT into packages table."""
        with pytest.raises(Exception) as exc_info:
            runtime_conn.execute(
                "INSERT INTO packages (code, name, release_status) "
                "VALUES ('rogue_pkg', 'Rogue Package', 'planned')"
            )
            runtime_conn.commit()

        runtime_conn.rollback()
        error_msg = str(exc_info.value).lower()
        assert any(
            phrase in error_msg
            for phrase in ["permission denied", "privilege", "denied"]
        ), f"T16 FAILED: Expected permission error on packages INSERT, got: {exc_info.value}"

    def test_runtime_can_read_packages(self, runtime_conn):
        """app_runtime MUST be able to SELECT from packages (needed for plan display)."""
        rows = runtime_conn.execute(
            "SELECT code FROM packages ORDER BY code"
        ).fetchall()
        # Should return all 10 packages
        assert len(rows) == 10, f"T16: Expected to read 10 packages, got {len(rows)}"
