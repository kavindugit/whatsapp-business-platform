# ADR 0002: Tenant Isolation Strategy

## Context
The platform is a multi-tenant SaaS application. We must ensure that data belonging to one tenant (workspace) is absolutely inaccessible to users of another tenant. Relying solely on application-level `WHERE tenant_id = X` clauses is prone to developer error and can lead to catastrophic data leaks.

## Decision
We will enforce tenant isolation at the database level using PostgreSQL Row-Level Security (RLS).
1. Every tenant-owned table (e.g., `business_settings`, `contacts`, `tenant_audit_events`) will have RLS enabled and forced.
2. The `app_runtime` database role will NEVER have `BYPASSRLS` or superuser privileges.
3. Access to tenant data requires setting a transaction-local configuration variable `app.tenant_id`.
4. We implement a central `tenant_transaction` context manager in `backend/app/db/tenant_context.py` which sets this variable for the duration of a database transaction.
5. `tenant_id` is derived exclusively from the authenticated user's session and verified memberships, never trusted from a client request payload.

## Rationale
- **Defense in Depth**: Even if an application developer forgets a `WHERE` clause, the database will return zero rows or block the insert/update.
- **Auditable**: The RLS policies (`CREATE POLICY`) are explicitly defined in the database schema migrations.
- **Connection Safety**: By using `set_config('app.tenant_id', ..., true)`, the context is tied to the transaction and automatically clears on commit or rollback, preventing leakage across pooled connections.

## Consequences
- Operations spanning multiple tenants (if ever needed) are restricted. Platform admin operations must be carefully designed to operate on control-plane tables or switch contexts appropriately.
- Performance overhead of RLS is generally negligible but must be monitored on very large tables.
