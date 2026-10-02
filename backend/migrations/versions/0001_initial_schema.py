"""Initial schema — Week 1 platform foundation.

Creates all Week 1 control-plane and tenant-owned tables, database roles,
row-level security policies, table grants, and package catalogue seed data.

Revision ID: 0001
Revises: None
Create Date: 2026-10-02

Design decisions (see docs/decisions/0002-tenant-isolation.md):
- migration_owner role owns all tables (created by db-init.sh)
- app_runtime role has only the minimum required grants
- app_runtime has no BYPASSRLS, no superuser, no table ownership
- RLS is ENABLED and FORCED on all tenant-owned tables
- RLS policy uses transaction-local set_config('app.tenant_id', ..., true)
- package_versions is immutable: no UPDATE/DELETE granted to app_runtime
- platform_audit_events and tenant_audit_events are append-only
"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Feature registry — all valid feature codes (W1-060) ───────────────────────
VALID_FEATURE_CODES = {
    "core_inbox",
    "contact_directory",
    "business_settings",
    "fixed_faq",
    "notification_triggers",
    "ai_answers",
    "knowledge_base",
    "catalogue",
    "order_capture",
    "calendar_booking",
    "lead_qualification",
    "ticketing",
    "store_connector",
    "campaign_segments",
    "branch_routing",
}

# ── Package seed data (W1-060) ────────────────────────────────────────────────
# All packages: version=1, release_status='planned', currency='LKR'
# Prices in minor units: 6900 LKR = 690000 minor units
PACKAGES = [
    {
        "code": "starter",
        "name": "Business Starter",
        "description": "Rule-based FAQ replies, enquiry capture, staff handover.",
        "monthly_price": 690000,
        "setup_price": 2000000,
        "staff_limit": 1,
        "number_limit": 1,
        "features": {"core_inbox", "contact_directory", "business_settings", "fixed_faq"},
        "metrics": {"rule_replies": 1000, "ai_credits": 0, "notification_sends": 0},
    },
    {
        "code": "updates",
        "name": "Customer Updates",
        "description": "Templated notifications and status updates to customers.",
        "monthly_price": 990000,
        "setup_price": 3500000,
        "staff_limit": 2,
        "number_limit": 1,
        "features": {"core_inbox", "contact_directory", "business_settings", "notification_triggers"},
        "metrics": {"rule_replies": 0, "ai_credits": 0, "notification_sends": 3000},
    },
    {
        "code": "receptionist",
        "name": "AI Receptionist",
        "description": "AI-grounded answers from approved FAQs and documents.",
        "monthly_price": 1290000,
        "setup_price": 4000000,
        "staff_limit": 2,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "fixed_faq", "ai_answers", "knowledge_base",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 1500, "notification_sends": 0},
    },
    {
        "code": "order_desk",
        "name": "WhatsApp Order Desk",
        "description": "Catalogue, order capture, fulfilment status and staff dashboard.",
        "monthly_price": 1990000,
        "setup_price": 6500000,
        "staff_limit": 3,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "fixed_faq", "ai_answers", "catalogue", "order_capture",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 3000, "notification_sends": 0, "orders": 500},
    },
    {
        "code": "appointments",
        "name": "Appointment Assistant",
        "description": "Service bookings, availability, reminders and calendar integration.",
        "monthly_price": 1990000,
        "setup_price": 6500000,
        "staff_limit": 3,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "fixed_faq", "ai_answers", "calendar_booking",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 3000, "notification_sends": 0, "bookings": 500},
    },
    {
        "code": "sales_leads",
        "name": "Sales and Lead Assistant",
        "description": "Lead qualification, routing and CRM integration.",
        "monthly_price": 2490000,
        "setup_price": 8500000,
        "staff_limit": 4,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "ai_answers", "lead_qualification",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 4000, "notification_sends": 0, "leads": 1000},
    },
    {
        "code": "support_team",
        "name": "Customer Support Team",
        "description": "Ticketing, departments, escalation and response metrics.",
        "monthly_price": 3490000,
        "setup_price": 10000000,
        "staff_limit": 5,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "ai_answers", "knowledge_base", "ticketing",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 6000, "notification_sends": 0, "tickets": 2000},
    },
    {
        "code": "connected_commerce",
        "name": "Connected Commerce",
        "description": "Live store connector, basket creation and payment events.",
        "monthly_price": 4990000,
        "setup_price": 15000000,
        "staff_limit": 5,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "ai_answers", "catalogue", "order_capture", "store_connector",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 10000, "notification_sends": 0, "orders": 2000},
    },
    {
        "code": "retention",
        "name": "Customer Retention",
        "description": "Campaigns, segments, AI replies and engagement reporting.",
        "monthly_price": 4490000,
        "setup_price": 10000000,
        "staff_limit": 5,
        "number_limit": 1,
        "features": {
            "core_inbox", "contact_directory", "business_settings",
            "notification_triggers", "ai_answers", "campaign_segments",
        },
        "metrics": {"rule_replies": 0, "ai_credits": 5000, "notification_sends": 10000},
    },
    {
        "code": "enterprise",
        "name": "Enterprise Operations",
        "description": "Multi-branch, 20 staff, 3 numbers, custom integrations and SLA.",
        "monthly_price": 14990000,
        "setup_price": 60000000,
        "staff_limit": 20,
        "number_limit": 3,
        "features": VALID_FEATURE_CODES,  # All features
        "metrics": {"rule_replies": 0, "ai_credits": 30000, "notification_sends": 0, "workflow_runs": 10000},
    },
]


def upgrade() -> None:
    # ── Extension ─────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── Control-plane tables ──────────────────────────────────────────────────

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'active'"),
                  comment="active | disabled"),
        sa.Column("system_role", sa.String(50), nullable=True,
                  comment="platform_admin | null"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint("char_length(display_name) BETWEEN 1 AND 120",
                           name="ck_users_display_name_length"),
        sa.CheckConstraint("status IN ('active', 'disabled')",
                           name="ck_users_status"),
        sa.CheckConstraint("system_role IS NULL OR system_role IN ('platform_admin')",
                           name="ck_users_system_role"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # auth_sessions
    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("csrf_token", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("absolute_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE",
                                name="fk_auth_sessions_user_id"),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
    )
    op.create_index(
        "ix_auth_sessions_token_hash_active", "auth_sessions", ["token_hash"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])

    # tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("legal_name", sa.String(200), nullable=True),
        sa.Column("industry_tag", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'active'")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$'",
            name="ck_tenants_slug_format",
        ),
        sa.CheckConstraint("char_length(display_name) BETWEEN 1 AND 120",
                           name="ck_tenants_display_name_length"),
        sa.CheckConstraint("status IN ('active', 'suspended')",
                           name="ck_tenants_status"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )

    # tenant_memberships
    op.create_table(
        "tenant_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                name="fk_tenant_memberships_tenant_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name="fk_tenant_memberships_user_id"),
        sa.CheckConstraint("role IN ('owner', 'manager', 'agent')",
                           name="ck_tenant_memberships_role"),
        sa.CheckConstraint("status IN ('active', 'inactive')",
                           name="ck_tenant_memberships_status"),
        sa.UniqueConstraint("tenant_id", "user_id",
                            name="uq_tenant_memberships_tenant_user"),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"])
    op.create_index("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"])
    # Partial unique index: at most one active owner per tenant (W1-043)
    op.create_index(
        "uq_tenant_memberships_active_owner",
        "tenant_memberships",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner' AND status = 'active'"),
    )

    # packages
    op.create_table(
        "packages",
        sa.Column("code", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("release_status", sa.String(20), nullable=False,
                  server_default=sa.text("'planned'")),
        sa.Column("description", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(
            "release_status IN ('planned', 'internal', 'pilot', 'saleable')",
            name="ck_packages_release_status",
        ),
    )

    # package_versions — IMMUTABLE after creation
    op.create_table(
        "package_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("package_code", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default=sa.text("'LKR'")),
        sa.Column("monthly_price", sa.BigInteger, nullable=False,
                  comment="LKR minor units (paise)"),
        sa.Column("setup_price", sa.BigInteger, nullable=False,
                  comment="LKR minor units (paise)"),
        sa.Column("staff_limit", sa.Integer, nullable=False),
        sa.Column("number_limit", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("feature_permissions", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("metric_limits", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["package_code"], ["packages.code"],
                                name="fk_package_versions_package_code"),
        sa.CheckConstraint("monthly_price >= 0", name="ck_package_versions_monthly_price"),
        sa.CheckConstraint("setup_price >= 0", name="ck_package_versions_setup_price"),
        sa.CheckConstraint("staff_limit > 0", name="ck_package_versions_staff_limit"),
        sa.CheckConstraint("number_limit > 0", name="ck_package_versions_number_limit"),
        sa.UniqueConstraint("package_code", "version",
                            name="uq_package_versions_code_version"),
    )

    # subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'trial'")),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anchor_day", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                name="fk_subscriptions_tenant_id"),
        sa.ForeignKeyConstraint(["package_version_id"], ["package_versions.id"],
                                name="fk_subscriptions_package_version_id"),
        sa.CheckConstraint(
            "status IN ('trial', 'active', 'past_due', 'suspended', 'cancelled')",
            name="ck_subscriptions_status",
        ),
        sa.CheckConstraint("anchor_day BETWEEN 1 AND 31",
                           name="ck_subscriptions_anchor_day"),
        sa.CheckConstraint("period_end > period_start",
                           name="ck_subscriptions_period_order"),
        sa.UniqueConstraint("tenant_id", name="uq_subscriptions_tenant_id"),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])

    # platform_audit_events — append-only
    op.create_table(
        "platform_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # Soft FKs — not enforced as DB constraints so records survive user deletion
    )
    op.create_index("ix_platform_audit_events_actor", "platform_audit_events", ["actor_user_id"])
    op.create_index("ix_platform_audit_events_tenant", "platform_audit_events", ["target_tenant_id"])
    op.create_index("ix_platform_audit_events_created", "platform_audit_events", ["created_at"])

    # ── Tenant-owned tables (RLS required) ────────────────────────────────────

    # business_settings
    op.create_table(
        "business_settings",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_name", sa.String(120), nullable=False),
        sa.Column("public_email", sa.String(254), nullable=True),
        sa.Column("public_phone", sa.String(30), nullable=True),
        sa.Column("address_text", sa.String(1000), nullable=True),
        sa.Column("time_zone", sa.String(60), nullable=False,
                  server_default=sa.text("'Asia/Colombo'")),
        sa.Column("currency", sa.String(3), nullable=False,
                  server_default=sa.text("'LKR'")),
        sa.Column("reply_language", sa.String(10), nullable=False,
                  server_default=sa.text("'auto'")),
        sa.Column("opening_hours", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("escalation_text", sa.String(1000), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                name="fk_business_settings_tenant_id"),
        sa.CheckConstraint("char_length(business_name) BETWEEN 1 AND 120",
                           name="ck_business_settings_name_length"),
        sa.CheckConstraint(
            "reply_language IN ('auto', 'en', 'si', 'ta')",
            name="ck_business_settings_reply_language",
        ),
    )

    # contacts
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("phone_e164", sa.String(30), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("preferred_lang", sa.String(10), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'active'")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                name="fk_contacts_tenant_id"),
        sa.CheckConstraint("char_length(display_name) BETWEEN 1 AND 120",
                           name="ck_contacts_display_name_length"),
        sa.CheckConstraint("status IN ('active', 'archived')",
                           name="ck_contacts_status"),
        sa.CheckConstraint(
            "preferred_lang IS NULL OR preferred_lang IN ('auto', 'en', 'si', 'ta')",
            name="ck_contacts_preferred_lang",
        ),
        # Composite unique for future composite FK references
        sa.UniqueConstraint("tenant_id", "id", name="uq_contacts_tenant_id"),
    )
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_tenant_updated", "contacts", ["tenant_id", "updated_at"])
    # Partial unique: phone uniqueness within a tenant for active contacts only (T25)
    op.create_index(
        "uq_contacts_phone_active_per_tenant",
        "contacts",
        ["tenant_id", "phone_e164"],
        unique=True,
        postgresql_where=sa.text("phone_e164 IS NOT NULL AND status = 'active'"),
    )

    # tenant_audit_events — append-only + RLS
    op.create_table(
        "tenant_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_tenant_audit_events_tenant", "tenant_audit_events", ["tenant_id"])
    op.create_index(
        "ix_tenant_audit_events_tenant_created",
        "tenant_audit_events",
        ["tenant_id", "created_at"],
    )

    # ── Row-Level Security (W1-030, W1-031) ───────────────────────────────────
    # Enable RLS on all tenant-owned tables
    # FORCE RLS applies even to table owners (migration_owner) — prevents accidental bypass
    for table in ("business_settings", "contacts", "tenant_audit_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    # RLS policy: tenant_id must match the transaction-local app.tenant_id setting
    # NULLIF(..., '') ensures missing/empty context returns NULL → no rows visible
    rls_expression = (
        "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    )
    for table in ("business_settings", "contacts", "tenant_audit_events"):
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
                USING ({rls_expression})
                WITH CHECK ({rls_expression})
        """)

    # ── Role grants (W1-030) ──────────────────────────────────────────────────
    # Control-plane: app_runtime can read/write specific columns but cannot
    # truncate, drop, disable RLS, or write package_version definitions
    op.execute("GRANT SELECT, INSERT ON users TO app_runtime")
    op.execute("GRANT UPDATE (password_hash, status, display_name, updated_at) ON users TO app_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON auth_sessions TO app_runtime")
    op.execute("GRANT SELECT ON tenants TO app_runtime")
    op.execute("GRANT INSERT, UPDATE ON tenants TO app_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON tenant_memberships TO app_runtime")
    # packages and package_versions: READ ONLY for app_runtime (seeded by migrations)
    op.execute("GRANT SELECT ON packages TO app_runtime")
    op.execute("GRANT SELECT ON package_versions TO app_runtime")
    # NO INSERT/UPDATE/DELETE on package_versions for app_runtime — immutable
    op.execute("GRANT SELECT, INSERT, UPDATE ON subscriptions TO app_runtime")
    op.execute("GRANT SELECT, INSERT ON platform_audit_events TO app_runtime")
    # NO UPDATE/DELETE on platform_audit_events — append-only

    # Tenant-owned: app_runtime can read/write within RLS constraints
    op.execute("GRANT SELECT, INSERT, UPDATE ON business_settings TO app_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON contacts TO app_runtime")
    op.execute("GRANT SELECT, INSERT ON tenant_audit_events TO app_runtime")
    # NO UPDATE/DELETE on tenant_audit_events — append-only

    # Sequence grants for UUID generation (if using serial fallback)
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_runtime")

    # ── Package catalogue seed (W1-060) ───────────────────────────────────────
    # All packages are version 1, release_status='planned'
    # Seeded by migration (not runtime API) — using migration_owner privileges
    for pkg in PACKAGES:
        # Validate all feature codes are in the registry
        for code in pkg["features"]:
            assert code in VALID_FEATURE_CODES, f"Unknown feature code: {code}"

        op.execute(
            sa.text("""
                INSERT INTO packages (code, name, release_status, description)
                VALUES (:code, :name, 'planned', :description)
                ON CONFLICT (code) DO NOTHING
            """),
            {
                "code": pkg["code"],
                "name": pkg["name"],
                "description": pkg["description"],
            },
        )
        op.execute(
            sa.text("""
                INSERT INTO package_versions
                    (package_code, version, currency, monthly_price, setup_price,
                     staff_limit, number_limit, feature_permissions, metric_limits)
                VALUES
                    (:code, 1, 'LKR', :monthly, :setup,
                     :staff, :numbers, :features::jsonb, :metrics::jsonb)
                ON CONFLICT (package_code, version) DO NOTHING
            """),
            {
                "code": pkg["code"],
                "monthly": pkg["monthly_price"],
                "setup": pkg["setup_price"],
                "staff": pkg["staff_limit"],
                "numbers": pkg["number_limit"],
                "features": json.dumps({k: True for k in pkg["features"]}),
                "metrics": json.dumps(pkg["metrics"]),
            },
        )


def downgrade() -> None:
    # Remove grants first
    for table in ("business_settings", "contacts", "tenant_audit_events"):
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop tables in reverse FK dependency order
    for table in [
        "tenant_audit_events",
        "contacts",
        "business_settings",
        "platform_audit_events",
        "subscriptions",
        "package_versions",
        "packages",
        "tenant_memberships",
        "tenants",
        "auth_sessions",
        "users",
    ]:
        op.drop_table(table)
