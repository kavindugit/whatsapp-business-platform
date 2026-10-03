"""
tests/integration/test_rls.py
T01, T02 — Row-Level Security isolation tests.

These tests MUST use real PostgreSQL with the app_runtime role and RLS enabled.
Never use SQLite. Never mock the database layer.

T01: Cross-tenant read isolation — querying contacts as tenant A returns ZERO rows from tenant B.
T02: Cross-tenant write rejection — inserting a contact with wrong tenant_id via RLS context
     returns only the inserted row under the correct context.

Test design:
- Uses the app_runtime role directly (same as production)
- Sets app.tenant_id via set_config('app.tenant_id', ..., true) in a real transaction
- Does NOT rely on application query filters — tests only the RLS mechanism
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

# ── Helpers ────────────────────────────────────────────────────────────────────


def get_migration_dsn() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL", "")
    if not url:
        pytest.skip("MIGRATION_DATABASE_URL not set — skipping RLS integration tests")
    # Convert SQLAlchemy URL prefix to libpq DSN for psycopg3
    return url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def get_runtime_dsn() -> str:
    url = os.environ.get("TEST_DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not url:
        pytest.skip("TEST_DATABASE_URL not set — skipping RLS integration tests")
    return url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def provision_test_tenant(
    migration_conn: psycopg.Connection,
    slug: str,
    display_name: str,
) -> uuid.UUID:
    """Create a tenant and its business_settings using the migration_owner role."""
    tenant_id = uuid.uuid4()
    migration_conn.execute(
        """
        INSERT INTO tenants (id, slug, display_name, industry_tag, status)
        VALUES (%s, %s, %s, 'test', 'active')
        """,
        (str(tenant_id), slug, display_name),
    )
    migration_conn.execute(
        """
        INSERT INTO business_settings (tenant_id, business_name)
        VALUES (%s, %s)
        """,
        (str(tenant_id), display_name),
    )
    return tenant_id


def provision_test_contact(
    migration_conn: psycopg.Connection,
    tenant_id: uuid.UUID,
    name: str,
    phone: str | None = None,
) -> uuid.UUID:
    """Create a contact using the migration_owner role (bypasses RLS as owner)."""
    contact_id = uuid.uuid4()
    migration_conn.execute(
        """
        INSERT INTO contacts (id, tenant_id, display_name, phone_e164, status)
        VALUES (%s, %s, %s, %s, 'active')
        """,
        (str(contact_id), str(tenant_id), name, phone),
    )
    return contact_id


@pytest.fixture(scope="module")
def migration_conn():
    """Synchronous psycopg3 connection as migration_owner for test setup."""
    dsn = get_migration_dsn()
    conn = psycopg.connect(dsn, autocommit=False)
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope="module")
def runtime_conn():
    """Synchronous psycopg3 connection as app_runtime (same role as production)."""
    dsn = get_runtime_dsn()
    conn = psycopg.connect(dsn, autocommit=False)
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope="module")
def two_tenants(migration_conn):
    """
    Provision two test tenants with contacts via migration_owner.
    Cleans up at end of module.
    """
    slug_a = f"rls-test-a-{uuid.uuid4().hex[:6]}"
    slug_b = f"rls-test-b-{uuid.uuid4().hex[:6]}"

    tenant_a = provision_test_tenant(migration_conn, slug_a, "RLS Test Tenant A")
    tenant_b = provision_test_tenant(migration_conn, slug_b, "RLS Test Tenant B")

    contact_a1 = provision_test_contact(migration_conn, tenant_a, "Alice A", "+94771000001")
    contact_a2 = provision_test_contact(migration_conn, tenant_a, "Bob A", "+94771000002")
    contact_b1 = provision_test_contact(migration_conn, tenant_b, "Charlie B", "+94771000003")

    migration_conn.commit()

    yield {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "contact_a1": contact_a1,
        "contact_a2": contact_a2,
        "contact_b1": contact_b1,
    }

    # Cleanup
    migration_conn.execute(
        "DELETE FROM contacts WHERE tenant_id IN (%s, %s)", (str(tenant_a), str(tenant_b))
    )
    migration_conn.execute(
        "DELETE FROM business_settings WHERE tenant_id IN (%s, %s)", (str(tenant_a), str(tenant_b))
    )
    migration_conn.execute(
        "DELETE FROM tenants WHERE id IN (%s, %s)", (str(tenant_a), str(tenant_b))
    )
    migration_conn.commit()


@pytest.mark.integration
class TestT01CrossTenantReadIsolation:
    """
    T01: Row-Level Security blocks cross-tenant reads.
    When app.tenant_id is set to tenant A, queries must return ZERO rows from tenant B.
    The RLS policy (not application filter) is the mechanism under test.
    """

    def test_tenant_a_sees_only_own_contacts(self, runtime_conn, two_tenants):
        """Querying as tenant A returns ONLY tenant A's contacts — zero from tenant B."""
        tenant_a = two_tenants["tenant_a"]
        tenant_b = two_tenants["tenant_b"]

        # Set transaction-local context to tenant A
        runtime_conn.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_a),),
        )

        # Query without any application-level tenant filter
        rows = runtime_conn.execute(
            "SELECT id, tenant_id FROM contacts ORDER BY created_at"
        ).fetchall()

        tenant_ids_returned = {str(row[1]) for row in rows}

        assert str(tenant_a) in tenant_ids_returned, "Should see own contacts"
        assert str(tenant_b) not in tenant_ids_returned, (
            "T01 FAILED: Tenant B rows visible under Tenant A context — RLS breach!"
        )
        assert len(rows) >= 2, "Should see at least the 2 contacts provisioned for tenant A"

    def test_tenant_b_sees_only_own_contacts(self, runtime_conn, two_tenants):
        """Querying as tenant B returns ONLY tenant B's contacts."""
        tenant_a = two_tenants["tenant_a"]
        tenant_b = two_tenants["tenant_b"]

        runtime_conn.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_b),),
        )

        rows = runtime_conn.execute(
            "SELECT id, tenant_id FROM contacts ORDER BY created_at"
        ).fetchall()

        tenant_ids_returned = {str(row[1]) for row in rows}

        assert str(tenant_b) in tenant_ids_returned, "Should see own contacts"
        assert str(tenant_a) not in tenant_ids_returned, (
            "T01 FAILED: Tenant A rows visible under Tenant B context — RLS breach!"
        )

    def test_no_context_returns_zero_rows(self, runtime_conn, two_tenants):
        """Without any tenant context, zero rows should be visible (NULLIF → NULL → no match)."""
        runtime_conn.execute("SELECT set_config('app.tenant_id', '', true)")

        rows = runtime_conn.execute("SELECT id FROM contacts").fetchall()

        assert len(rows) == 0, (
            "T01 FAILED: Rows visible with no tenant context — RLS policy is broken!"
        )

    def test_business_settings_also_isolated(self, runtime_conn, two_tenants):
        """RLS also isolates business_settings (W1-030)."""
        tenant_a = two_tenants["tenant_a"]
        tenant_b = two_tenants["tenant_b"]

        runtime_conn.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_a),),
        )

        rows = runtime_conn.execute("SELECT tenant_id FROM business_settings").fetchall()

        tenant_ids = {str(row[0]) for row in rows}
        assert str(tenant_b) not in tenant_ids, (
            "T01 FAILED: Tenant B business_settings visible under Tenant A context!"
        )


@pytest.mark.integration
class TestT02CrossTenantWriteIsolation:
    """
    T02: Row-Level Security blocks cross-tenant writes via WITH CHECK.
    When app.tenant_id is set to tenant A, attempting to INSERT a contact
    with tenant_id=B must fail.
    """

    def test_write_to_wrong_tenant_is_rejected(self, runtime_conn, two_tenants):
        """
        Attempting to INSERT a contact with a different tenant_id than the RLS context
        must raise an exception (RLS WITH CHECK clause).
        """
        tenant_a = two_tenants["tenant_a"]
        tenant_b = two_tenants["tenant_b"]

        # Set context to tenant A
        runtime_conn.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_a),),
        )

        # Attempt to insert a contact with tenant_b's ID (cross-tenant write)
        with pytest.raises(Exception) as exc_info:
            runtime_conn.execute(
                """
                INSERT INTO contacts (id, tenant_id, display_name, status)
                VALUES (gen_random_uuid(), %s, 'Rogue Contact', 'active')
                """,
                (str(tenant_b),),
            )
            runtime_conn.commit()

        # Should raise a PostgreSQL error (new row violates RLS policy)
        error_msg = str(exc_info.value).lower()
        assert any(
            phrase in error_msg for phrase in ["policy", "violates", "permission", "check"]
        ), f"T02 FAILED: Expected RLS policy error, got: {exc_info.value}"

        # Rollback for safety
        runtime_conn.rollback()

    def test_write_to_correct_tenant_succeeds(self, runtime_conn, two_tenants):
        """Writing a contact under the correct RLS context must succeed."""
        tenant_a = two_tenants["tenant_a"]
        contact_id = uuid.uuid4()

        runtime_conn.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_a),),
        )
        runtime_conn.execute(
            """
            INSERT INTO contacts (id, tenant_id, display_name, status)
            VALUES (%s, %s, 'Valid Contact', 'active')
            """,
            (str(contact_id), str(tenant_a)),
        )

        # Verify insert is visible under same context
        row = runtime_conn.execute(
            "SELECT id FROM contacts WHERE id = %s",
            (str(contact_id),),
        ).fetchone()

        assert row is not None, "T02: Contact insert should succeed under correct tenant context"
        runtime_conn.rollback()  # Don't persist test data
