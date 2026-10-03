#!/usr/bin/env bash
# scripts/db-init.sh
# Runs once when the PostgreSQL container is first created.
# Creates the two application roles and the test database.
# Passwords come from environment variables set in compose.yaml.
# Tables are created by Alembic migrations, not this script.

set -euo pipefail

MIGRATION_USER="${POSTGRES_MIGRATION_USER:-migration_owner}"
MIGRATION_PASS="${POSTGRES_MIGRATION_PASSWORD}"
RUNTIME_USER="${POSTGRES_RUNTIME_USER:-app_runtime}"
RUNTIME_PASS="${POSTGRES_RUNTIME_PASSWORD}"
TEST_DB="${TEST_POSTGRES_DB:-wbp_test}"
DEV_DB="${POSTGRES_DB:-wbp_dev}"

echo "[db-init] Creating roles and test database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DEV_DB" <<-EOSQL
    -- Migration owner role: owns all tables, runs Alembic
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${MIGRATION_USER}') THEN
            CREATE ROLE ${MIGRATION_USER} WITH LOGIN PASSWORD '${MIGRATION_PASS}' BYPASSRLS;
        END IF;
    END
    \$\$;

    -- Application runtime role: no superuser, no BYPASSRLS, no table ownership
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${RUNTIME_USER}') THEN
            CREATE ROLE ${RUNTIME_USER} WITH LOGIN PASSWORD '${RUNTIME_PASS}' NOINHERIT;
        END IF;
    END
    \$\$;

    -- Schema access grants
    GRANT ALL ON SCHEMA public TO ${MIGRATION_USER};
    GRANT USAGE ON SCHEMA public TO ${RUNTIME_USER};

    -- Verify runtime role has no dangerous privileges
    DO \$\$
    DECLARE
        r pg_roles%ROWTYPE;
    BEGIN
        SELECT * INTO r FROM pg_roles WHERE rolname = '${RUNTIME_USER}';
        IF r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb THEN
            RAISE EXCEPTION 'app_runtime role has unexpected privileges';
        END IF;
    END
    \$\$;
EOSQL

# Create test database if it does not exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE ${TEST_DB} OWNER ${MIGRATION_USER}'
    WHERE NOT EXISTS (
        SELECT FROM pg_database WHERE datname = '${TEST_DB}'
    )\gexec

    GRANT USAGE ON SCHEMA public TO ${RUNTIME_USER};
EOSQL

# Grant runtime user schema access on test DB too
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$TEST_DB" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO ${RUNTIME_USER};
EOSQL

echo "[db-init] Done. Roles created; tables will be created by Alembic migrations."
