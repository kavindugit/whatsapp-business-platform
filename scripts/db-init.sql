-- Database initialisation script
-- Runs ONCE when the PostgreSQL container is first created (docker-entrypoint-initdb.d).
-- This script creates the two application roles and the test database.
-- Passwords are injected via environment variables in compose.yaml.
-- This script does NOT create tables — Alembic migrations handle the schema.

-- Create the migration owner role (owns tables, runs Alembic)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'migration_owner') THEN
        EXECUTE format(
            'CREATE ROLE migration_owner WITH LOGIN PASSWORD %L',
            current_setting('app.migration_password', true)
        );
    END IF;
END
$$;

-- Create the application runtime role (no superuser, no BYPASSRLS, no table ownership)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_runtime') THEN
        EXECUTE format(
            'CREATE ROLE app_runtime WITH LOGIN PASSWORD %L NOINHERIT',
            current_setting('app.runtime_password', true)
        );
    END IF;
END
$$;

-- Grant migration_owner the ability to create objects in the public schema
GRANT ALL ON SCHEMA public TO migration_owner;

-- Grant app_runtime usage on the public schema (object grants done by Alembic migration)
GRANT USAGE ON SCHEMA public TO app_runtime;

-- Create the test database (separate from development)
SELECT 'CREATE DATABASE wbp_test OWNER migration_owner'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'wbp_test')\gexec
