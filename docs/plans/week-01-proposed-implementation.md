# Week 1 — Proposed Implementation Plan

**Project:** WhatsApp Business Automation Platform  
**Prepared:** 2026-10-02 | **Companion specs:** `PROJECT_BLUEPRINT.md`, `WEEK_01_IMPLEMENTATION_SPEC.md`  
**Status:** Awaiting founder review before any implementation begins.

---

## 1. Repository Inventory

| Path | State | Action |
|---|---|---|
| `README.md` | 1-line stub (`# whatsapp-business-platform`) | Expand per W1-100 |
| `.gitignore` | Present (4.8 KB, standard Node/Python) | Extend with additional ignores listed below |
| `PROJECT_BLUEPRINT.md` | Present (planning only) | Move to `docs/` |
| `WEEK_01_IMPLEMENTATION_SPEC.md` | Present (planning only) | Move to `docs/` |
| `.git/` | Initialised, no commits | First commit will be this proposal |
| Everything else | Absent | Create per plan below |

**Existing work to preserve:** None beyond the two spec documents. They will be relocated to `docs/` (not deleted) and referenced in README.

**Additional `.gitignore` entries required:**
```
.env
*.env.local
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
htmlcov/
dist/
node_modules/
frontend/dist/
*.egg-info/
*.db
*.sqlite3
uploads/
local-reports/
playwright-report/
test-results/
```

---

## 2. Runtime and Library Versions

All versions selected are current stable releases as of 2026-10-01. Exact versions will be pinned in lockfiles.

### Backend (Python)

| Library | Version | Purpose |
|---|---|---|
| Python | 3.12.x | Runtime; matches Docker `python:3.12-slim` |
| FastAPI | 0.115.x | ASGI web framework |
| Uvicorn | 0.32.x | ASGI server (with `uvicorn[standard]`) |
| Pydantic | 2.9.x | Validation and settings |
| SQLAlchemy | 2.0.x | ORM and core SQL |
| Alembic | 1.14.x | Schema migrations |
| psycopg | 3.2.x | PostgreSQL async driver (`psycopg[binary,pool]`) |
| argon2-cffi | 23.1.x | Argon2id password hashing |
| redis | 5.2.x | Login throttle counters |
| pydantic-settings | 2.6.x | Configuration from env |
| phonenumbers | 8.13.x | E.164 normalisation |
| email-validator | 2.2.x | Email canonicalisation |
| zoneinfo | stdlib (3.12) | IANA time zone validation |
| structlog | 24.x | Structured JSON logging |
| Ruff | 0.8.x | Linting and formatting |
| mypy | 1.13.x | Type checking |
| pytest | 8.3.x | Test runner |
| pytest-asyncio | 0.24.x | Async test support |
| httpx | 0.28.x | Test client for FastAPI |
| factory-boy | 3.3.x | Fixture factories |
| uv | 0.5.x | Dependency management and lockfile |

**Package manager:** `uv` — produces `uv.lock` (committed). `pyproject.toml` with dependency groups (`dev`, `test`).

### Frontend (Node/React)

| Library | Version | Purpose |
|---|---|---|
| Node.js | 22.x LTS | Runtime |
| pnpm | 9.x | Package manager; produces `pnpm-lock.yaml` (committed) |
| React | 19.x | UI library |
| TypeScript | 5.7.x | Strict mode |
| Vite | 6.x | Dev server and bundler |
| React Router | 7.x | Client-side routing |
| TanStack Query | 5.x | Server state / cache management |
| Axios | 1.7.x | HTTP client (typed, interceptor-based) |
| React Hook Form | 7.x | Form management |
| Zod | 3.x | Runtime schema validation |
| ESLint | 9.x | Linting (flat config) |
| Prettier | 3.x | Formatting |
| Vitest | 2.x | Unit test runner |
| React Testing Library | 16.x | Component tests |
| Playwright | 1.49.x | Browser smoke tests |

### Infrastructure

| Service | Version | Notes |
|---|---|---|
| PostgreSQL | 17 | Docker image `postgres:17-alpine` |
| Redis | 7.4 | Docker image `redis:7.4-alpine` |
| Docker Desktop | Latest stable | Windows WSL2 backend required |

---

## 3. Planned File Tree

```text
whatsapp-business-platform/
├── README.md                          # Full startup guide (W1-100)
├── AGENTS.md                          # Coding agent operating contract (W1-100)
├── .gitignore                         # Extended
├── .env.example                       # Placeholders only (W1-012)
├── compose.yaml                       # PostgreSQL, Redis, API, Web (W1-011)
│
├── backend/
│   ├── pyproject.toml                 # Dependencies + tool config
│   ├── uv.lock                        # Committed lockfile
│   ├── Dockerfile                     # Multi-stage build
│   ├── alembic.ini                    # Points to migrations/
│   ├── migrations/
│   │   ├── env.py                     # Uses migration_owner URL
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial_schema.py # All W1 tables + RLS + grants
│   └── app/
│       ├── main.py                    # FastAPI app factory, middleware, routers
│       ├── cli.py                     # Typer CLI (operator provision, seed, etc.)
│       ├── core/
│       │   ├── config.py              # pydantic-settings; validates all required vars
│       │   ├── clock.py               # Injectable UTC clock (testable)
│       │   ├── errors.py              # Error envelope, exception handlers, request IDs
│       │   ├── logging.py             # structlog configuration, request middleware
│       │   └── security.py            # CSRF, Origin validation, cookie helpers
│       ├── db/
│       │   ├── base.py                # SQLAlchemy Base, UUID convention
│       │   ├── session.py             # Engine factory; app_runtime role pool
│       │   ├── tenant_context.py      # tenant_transaction() helper (W1-031)
│       │   └── models/
│       │       ├── users.py           # User, AuthSession (W1-021)
│       │       ├── tenants.py         # Tenant, TenantMembership (W1-021)
│       │       ├── plans.py           # Package, PackageVersion, Subscription (W1-021)
│       │       ├── settings.py        # BusinessSettings (W1-022)
│       │       ├── contacts.py        # Contact (W1-022)
│       │       └── audit.py           # PlatformAuditEvent, TenantAuditEvent (W1-021/022)
│       └── modules/
│           ├── auth/
│           │   ├── router.py          # /auth/login, /auth/logout, /auth/me
│           │   ├── service.py         # Login, session create/revoke, me
│           │   ├── throttle.py        # Redis-backed rate limiter
│           │   ├── dependencies.py    # get_current_user, require_session, csrf_check
│           │   └── schemas.py         # LoginRequest, UserSummary, MeResponse
│           ├── tenancy/
│           │   ├── router.py          # /admin/tenants/*, /tenants/{id}/settings, /members
│           │   ├── service.py         # Workspace create, suspend, settings CRUD
│           │   ├── dependencies.py    # require_membership, require_role, check_suspension
│           │   └── schemas.py         # TenantDTO, SettingsDTO, MemberDTO
│           ├── plans/
│           │   ├── router.py          # GET /packages, /tenants/{id}/subscription
│           │   ├── service.py         # Catalogue query, entitlement check
│           │   ├── entitlements.py    # require_feature() helper
│           │   └── schemas.py         # PackageDTO, SubscriptionDTO
│           ├── contacts/
│           │   ├── router.py          # /tenants/{id}/contacts/* CRUD
│           │   ├── service.py         # Contact CRUD, archive/restore
│           │   └── schemas.py         # ContactDTO, ContactCreate, ContactUpdate
│           └── audit/
│               └── service.py         # Append-only audit writers
│
├── frontend/
│   ├── package.json
│   ├── pnpm-lock.yaml                 # Committed lockfile
│   ├── tsconfig.json                  # Strict mode
│   ├── vite.config.ts                 # /api proxy to API container
│   ├── eslint.config.js               # ESLint flat config
│   ├── playwright.config.ts           # Browser smoke tests
│   ├── Dockerfile
│   └── src/
│       ├── main.tsx                   # React entry point
│       ├── app/
│       │   ├── App.tsx                # Router setup
│       │   ├── AuthContext.tsx        # Current user + CSRF state
│       │   └── WorkspaceContext.tsx   # Active tenant + cache invalidation
│       ├── api/
│       │   ├── client.ts              # Axios instance; CSRF header injection
│       │   ├── auth.ts                # Login, logout, me
│       │   ├── tenants.ts             # Admin + tenant endpoints
│       │   ├── contacts.ts            # Contact CRUD
│       │   ├── plans.ts               # Packages + subscription
│       │   └── errors.ts              # Error envelope parser
│       ├── components/
│       │   ├── AppShell.tsx           # Sidebar, nav, workspace selector, logout
│       │   ├── ProtectedRoute.tsx     # Auth + role gate
│       │   ├── ErrorBoundary.tsx
│       │   ├── LoadingState.tsx
│       │   ├── EmptyState.tsx
│       │   ├── ConfirmDialog.tsx
│       │   └── ui/                    # Button, Input, Badge, Card, Table, etc.
│       └── features/
│           ├── auth/
│           │   └── LoginPage.tsx
│           ├── workspaces/
│           │   └── WorkspacesPage.tsx
│           ├── admin/
│           │   └── TenantsPage.tsx
│           ├── overview/
│           │   └── OverviewPage.tsx
│           ├── settings/
│           │   └── SettingsPage.tsx
│           ├── contacts/
│           │   ├── ContactsPage.tsx
│           │   ├── ContactForm.tsx
│           │   └── ContactRow.tsx
│           ├── team/
│           │   └── TeamPage.tsx
│           └── plan/
│               └── PlanPage.tsx
│
├── docs/
│   ├── PROJECT_BLUEPRINT.md           # Moved from root
│   ├── WEEK_01_IMPLEMENTATION_SPEC.md # Moved from root
│   ├── plans/
│   │   └── week-01-proposed-implementation.md   # This file
│   ├── decisions/
│   │   ├── 0001-platform-and-stack.md
│   │   ├── 0002-tenant-isolation.md
│   │   └── 0003-auth-sessions.md
│   └── reports/
│       └── week-01-completion.md      # Filled after implementation
│
├── scripts/
│   ├── migrate.ps1                    # Runs Alembic via migration_owner creds
│   └── seed-demo.ps1                  # Dev/test seed wrapper
│
└── .github/
    └── workflows/
        └── ci.yml                     # CI pipeline (W1-013)
```

---

## 4. Database Schema Design

### 4.1 Control-Plane Tables (W1-021)

#### `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120),
    password_hash   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled')),
    system_role     TEXT CHECK (system_role IN ('platform_admin')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `auth_sessions`
```sql
CREATE TABLE auth_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      TEXT NOT NULL UNIQUE,
    csrf_token      TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    absolute_expiry TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ
);
CREATE INDEX ON auth_sessions(token_hash) WHERE revoked_at IS NULL;
CREATE INDEX ON auth_sessions(user_id);
```

#### `tenants`
```sql
CREATE TABLE tenants (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug         TEXT NOT NULL UNIQUE
                 CHECK (slug ~ '^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$'),
    display_name TEXT NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120),
    legal_name   TEXT CHECK (char_length(legal_name) <= 200),
    industry_tag TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended')),
    version      INTEGER NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `tenant_memberships`
```sql
CREATE TABLE tenant_memberships (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  UUID NOT NULL REFERENCES tenants(id),
    user_id    UUID NOT NULL REFERENCES users(id),
    role       TEXT NOT NULL CHECK (role IN ('owner','manager','agent')),
    status     TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, user_id)
);
CREATE UNIQUE INDEX uq_tenant_active_owner
    ON tenant_memberships(tenant_id)
    WHERE role = 'owner' AND status = 'active';
```

#### `packages`
```sql
CREATE TABLE packages (
    code           TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    release_status TEXT NOT NULL DEFAULT 'planned'
                   CHECK (release_status IN ('planned','internal','pilot','saleable')),
    description    TEXT NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `package_versions`
```sql
CREATE TABLE package_versions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_code        TEXT NOT NULL REFERENCES packages(code),
    version             INTEGER NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'LKR',
    monthly_price       BIGINT NOT NULL,
    setup_price         BIGINT NOT NULL,
    staff_limit         INTEGER NOT NULL,
    number_limit        INTEGER NOT NULL DEFAULT 1,
    feature_permissions JSONB NOT NULL DEFAULT '{}',
    metric_limits       JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (package_code, version)
);
-- Immutable: no UPDATE/DELETE granted to app_runtime
```

#### `subscriptions`
```sql
CREATE TABLE subscriptions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id          UUID NOT NULL UNIQUE REFERENCES tenants(id),
    package_version_id UUID NOT NULL REFERENCES package_versions(id),
    status             TEXT NOT NULL DEFAULT 'trial'
                       CHECK (status IN ('trial','active','past_due','suspended','cancelled')),
    period_start       TIMESTAMPTZ NOT NULL,
    period_end         TIMESTAMPTZ NOT NULL,
    anchor_day         INTEGER NOT NULL CHECK (anchor_day BETWEEN 1 AND 31),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `platform_audit_events`
```sql
CREATE TABLE platform_audit_events (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id    UUID REFERENCES users(id),
    action           TEXT NOT NULL,
    target_tenant_id UUID REFERENCES tenants(id),
    target_user_id   UUID REFERENCES users(id),
    request_id       TEXT,
    metadata         JSONB NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Append-only: no UPDATE/DELETE granted to app_runtime
```

### 4.2 Tenant-Owned Tables with RLS (W1-022)

#### `business_settings`
```sql
CREATE TABLE business_settings (
    tenant_id       UUID PRIMARY KEY REFERENCES tenants(id),
    business_name   TEXT NOT NULL CHECK (char_length(business_name) BETWEEN 1 AND 120),
    public_email    TEXT CHECK (char_length(public_email) <= 254),
    public_phone    TEXT,
    address_text    TEXT CHECK (char_length(address_text) <= 1000),
    time_zone       TEXT NOT NULL DEFAULT 'Asia/Colombo',
    currency        TEXT NOT NULL DEFAULT 'LKR',
    reply_language  TEXT NOT NULL DEFAULT 'auto'
                    CHECK (reply_language IN ('auto','en','si','ta')),
    opening_hours   JSONB NOT NULL DEFAULT '{}',
    escalation_text TEXT CHECK (char_length(escalation_text) <= 1000),
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE business_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_settings FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON business_settings
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
```

#### `contacts`
```sql
CREATE TABLE contacts (
    id             UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenants(id),
    display_name   TEXT NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120),
    phone_e164     TEXT,
    email          TEXT CHECK (char_length(email) <= 254),
    preferred_lang TEXT CHECK (preferred_lang IN ('auto','en','si','ta')),
    notes          TEXT CHECK (char_length(notes) <= 1000),
    status         TEXT NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active','archived')),
    version        INTEGER NOT NULL DEFAULT 1,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE (tenant_id, id)
);

CREATE UNIQUE INDEX uq_contact_phone_active_per_tenant
    ON contacts(tenant_id, phone_e164)
    WHERE phone_e164 IS NOT NULL AND status = 'active';

ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON contacts
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
```

#### `tenant_audit_events`
```sql
CREATE TABLE tenant_audit_events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL,
    actor_user_id UUID REFERENCES users(id),
    action        TEXT NOT NULL,
    target_type   TEXT,
    target_id     UUID,
    request_id    TEXT,
    metadata      JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tenant_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_audit_events FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON tenant_audit_events
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
```

### 4.3 Database Roles and Grants (W1-030)

```sql
-- Roles created by migration tooling; passwords from environment, never committed SQL
CREATE ROLE migration_owner WITH LOGIN PASSWORD '<from_env>';
CREATE ROLE app_runtime WITH LOGIN PASSWORD '<from_env>';

-- app_runtime: no superuser, no BYPASSRLS, no table ownership, no schema creation

-- Control-plane grants (app_runtime):
GRANT SELECT, INSERT ON users TO app_runtime;
GRANT SELECT, INSERT, UPDATE ON auth_sessions TO app_runtime;
GRANT SELECT, INSERT, UPDATE ON tenants TO app_runtime;
GRANT SELECT, INSERT, UPDATE ON tenant_memberships TO app_runtime;
GRANT SELECT ON packages TO app_runtime;
GRANT SELECT ON package_versions TO app_runtime;   -- no INSERT/UPDATE/DELETE
GRANT SELECT, INSERT, UPDATE ON subscriptions TO app_runtime;
GRANT SELECT, INSERT ON platform_audit_events TO app_runtime;  -- no UPDATE/DELETE

-- Tenant-owned grants (governed by RLS):
GRANT SELECT, INSERT, UPDATE ON business_settings TO app_runtime;
GRANT SELECT, INSERT, UPDATE ON contacts TO app_runtime;
GRANT SELECT, INSERT ON tenant_audit_events TO app_runtime;    -- no UPDATE/DELETE
```

**Verification query (T02):**
```sql
SELECT rolsuper, rolinherit, rolbypassrls, rolcreaterole, rolcreatedb
FROM pg_roles WHERE rolname = 'app_runtime';
-- All must be false
```

---

## 5. Tenant Transaction Helper (W1-031)

Located at `backend/app/db/tenant_context.py`:

```python
# Conceptual design
from contextlib import asynccontextmanager
from uuid import UUID
import sqlalchemy as sa

@asynccontextmanager
async def tenant_transaction(conn, tenant_id: UUID):
    """
    1. Starts a transaction on the provided connection.
    2. Sets transaction-local app.tenant_id via bound parameter.
    3. Yields for callers to execute queries.
    4. Commits on success; rolls back on any exception.
    Context is automatically cleared at transaction end (true = transaction-local).
    """
    async with conn.begin():
        await conn.execute(
            sa.text("SELECT set_config('app.tenant_id', :tid, true)"),
            {"tid": str(tenant_id)}
        )
        yield conn
        # transaction-local setting auto-clears after commit/rollback
```

**Critical invariants:**
- `tenant_id` is always the server-validated UUID from authenticated membership — never from a request body.
- `set_config(..., true)` makes the setting transaction-local; it resets to `''` after commit/rollback, preventing leakage across pooled connections.
- No `disable_tenant_checks`, `is_admin_bypass`, or optional override mechanism.
- New tenant provisioning: server generates UUID, sets it as context before scoped writes, all within a single atomic transaction.

---

## 6. Authentication / Session / CSRF Design (W1-040, W1-041)

### Session Token Flow

```
POST /auth/login (JSON + allowed Origin)
  → Throttle check (Redis: email + IP counters)
  → Argon2id verify (or dummy hash for unknown email)
  → Generate 32-byte cryptographic random token (secrets.token_bytes(32))
  → Store SHA-256(token) in auth_sessions + random CSRF token
  → Set HttpOnly SameSite=Lax cookie
  → Return safe user summary + CSRF token in body
```

| Property | Value |
|---|---|
| Token entropy | 256 bits (32 bytes from `secrets.token_bytes`) |
| Stored form | `SHA-256(raw_token)` hex digest — never raw token |
| Cookie name | `session` |
| Cookie flags | `HttpOnly`, `SameSite=Lax`, `Path=/`, host-only |
| Secure flag | Required in production (`APP_ENV=production`) |
| Idle timeout | 30 minutes — enforced against `last_seen_at` |
| Absolute timeout | 12 hours — enforced against `created_at` |
| CSRF token | Separate random value stored in `auth_sessions`; returned in responses |
| CSRF verification | `X-CSRF-Token` header; `hmac.compare_digest()` constant-time compare |

### CSRF Strategy

| Endpoint type | Protection |
|---|---|
| `POST /auth/login` | Requires `Content-Type: application/json` + allowed `Origin` |
| All other unsafe methods | Requires `X-CSRF-Token` header + allowed `Origin` |
| GET / HEAD / OPTIONS | No CSRF required (read-only) |
| Logout | Requires CSRF even though destructive to session |

- Origin validated against `ALLOWED_ORIGINS` config — never trusted from `Host` or forwarded headers.
- No wildcard credentialed CORS.

### Login Throttling (Redis)

| Counter key | Limit | Window | On breach |
|---|---|---|---|
| `throttle:email:<hmac(email)>` | 5 failures | 15 min | 429 |
| `throttle:ip:<hmac(remote_addr)>` | 20 failures | 15 min | 429 |
| Redis unavailable | — | — | 503 (new logins fail; existing sessions continue) |

- Keys use HMAC with server secret for pseudonymisation.
- IP sourced from `REMOTE_ADDR` only (not `X-Forwarded-For` unless explicit trusted proxy config).
- Boundary: at exactly 5th failure the counter reaches 5; 6th request sees count ≥ 5 → 429.

### Argon2id Parameters
```
time_cost=2, memory_cost=65536 (64 MB), parallelism=2, hash_len=32
```
Minimum OWASP-aligned parameters. Document adjustment path in `docs/decisions/0003-auth-sessions.md`.

---

## 7. API Endpoint Plan (W1-050)

All authenticated routes validate: cookie exists → session not revoked → idle/absolute expiry → user active status.

| Req ID | Method + Path | Auth | Key behaviour |
|---|---|---|---|
| W1-050 | `GET /api/health/live` | None | Process up only; no DB/secrets |
| W1-050 | `GET /api/health/ready` | None | Checks DB + Redis; 503 if either down |
| W1-040 | `POST /api/v1/auth/login` | None | Origin+JSON; throttle; Argon2id; cookie+CSRF |
| W1-040 | `POST /api/v1/auth/logout` | Session+CSRF | Revoke session; clear cookie |
| W1-040 | `GET /api/v1/auth/me` | Session | User summary, memberships, CSRF token |
| W1-042 | `GET /api/v1/admin/tenants` | platform_admin | Paginated metadata; no contacts |
| W1-043 | `POST /api/v1/admin/tenants` | platform_admin | Atomic: tenant+sub+owner+settings |
| W1-042 | `PATCH /api/v1/admin/tenants/{tenant_id}/status` | platform_admin | Suspend/reactivate + version + audit |
| W1-042 | `GET /api/v1/admin/tenants/{tenant_id}` | platform_admin | Metadata + provisioning status |
| W1-060 | `GET /api/v1/packages` | Session | Catalogue + planned availability |
| W1-050 | `GET /api/v1/tenants/{tenant_id}/settings` | Membership | Settings DTO + version |
| W1-050 | `PATCH /api/v1/tenants/{tenant_id}/settings` | Owner/Manager | Allowlisted fields; optimistic lock; audit |
| W1-042 | `GET /api/v1/tenants/{tenant_id}/members` | Owner/Manager | Staff list; no hashes |
| W1-061 | `GET /api/v1/tenants/{tenant_id}/subscription` | Owner/Manager | Package version; trial/status; usage="N/A" |
| W1-022 | `GET /api/v1/tenants/{tenant_id}/contacts` | Membership | Paginated; search; status filter |
| W1-022 | `POST /api/v1/tenants/{tenant_id}/contacts` | Membership | Validated; tenant from context; 201 |
| W1-022 | `GET /api/v1/tenants/{tenant_id}/contacts/{contact_id}` | Membership | Own record or 404 |
| W1-022 | `PATCH /api/v1/tenants/{tenant_id}/contacts/{contact_id}` | Membership | Allowlisted fields; optimistic lock |
| W1-022 | `POST /api/v1/tenants/{tenant_id}/contacts/{contact_id}/archive` | Owner/Manager | Safe repeat state; version check |
| W1-022 | `POST /api/v1/tenants/{tenant_id}/contacts/{contact_id}/restore` | Owner/Manager | Version check; phone conflict handling |

### Error Envelope (all routes)
```json
{
  "error": {
    "code": "VERSION_CONFLICT",
    "message": "This record changed. Refresh and try again.",
    "details": []
  },
  "request_id": "server-generated-uuid"
}
```
- `request_id` generated server-side; echoed in `X-Request-ID` response header.
- Never returns stack traces, SQL, raw errors, or credentials.
- OpenAPI documents all 400/401/403/404/409/422/429/503 shapes.

---

## 8. Package Seed Definitions (W1-060)

All packages: `release_status = 'planned'`, `version = 1`. All prices in LKR minor units (÷100 for display).

| Code | Name | Monthly | Setup | Staff | Numbers | AI credits | Other limits |
|---|---|---|---|---|---|---|---|
| `starter` | Business Starter | 690,000 | 2,000,000 | 1 | 1 | 0 | rule_replies: 1,000 |
| `updates` | Customer Updates | 990,000 | 3,500,000 | 2 | 1 | 0 | notification_sends: 3,000 |
| `receptionist` | AI Receptionist | 1,290,000 | 4,000,000 | 2 | 1 | 1,500 | — |
| `order_desk` | WhatsApp Order Desk | 1,990,000 | 6,500,000 | 3 | 1 | 3,000 | orders: 500 |
| `appointments` | Appointment Assistant | 1,990,000 | 6,500,000 | 3 | 1 | 3,000 | bookings: 500 |
| `sales_leads` | Sales and Lead Assistant | 2,490,000 | 8,500,000 | 4 | 1 | 4,000 | leads: 1,000 |
| `support_team` | Customer Support Team | 3,490,000 | 10,000,000 | 5 | 1 | 6,000 | tickets: 2,000 |
| `connected_commerce` | Connected Commerce | 4,990,000 | 15,000,000 | 5 | 1 | 10,000 | orders: 2,000 |
| `retention` | Customer Retention | 4,490,000 | 10,000,000 | 5 | 1 | 5,000 | notification_sends: 10,000 |
| `enterprise` | Enterprise Operations | 14,990,000 | 60,000,000 | 20 | 3 | 30,000 | workflow_runs: 10,000 |

**Validated feature registry codes:**
`core_inbox`, `contact_directory`, `business_settings`, `fixed_faq`, `notification_triggers`, `ai_answers`, `knowledge_base`, `catalogue`, `order_capture`, `calendar_booking`, `lead_qualification`, `ticketing`, `store_connector`, `campaign_segments`, `branch_routing`

**Feature permissions by package:**

| Package | Features granted |
|---|---|
| `starter` | `core_inbox`, `contact_directory`, `business_settings`, `fixed_faq` |
| `updates` | `core_inbox`, `contact_directory`, `business_settings`, `notification_triggers` |
| `receptionist` | `core_inbox`, `contact_directory`, `business_settings`, `fixed_faq`, `ai_answers`, `knowledge_base` |
| `order_desk` | `core_inbox`, `contact_directory`, `business_settings`, `fixed_faq`, `ai_answers`, `catalogue`, `order_capture` |
| `appointments` | `core_inbox`, `contact_directory`, `business_settings`, `fixed_faq`, `ai_answers`, `calendar_booking` |
| `sales_leads` | `core_inbox`, `contact_directory`, `business_settings`, `ai_answers`, `lead_qualification` |
| `support_team` | `core_inbox`, `contact_directory`, `business_settings`, `ai_answers`, `knowledge_base`, `ticketing` |
| `connected_commerce` | `core_inbox`, `contact_directory`, `business_settings`, `ai_answers`, `catalogue`, `order_capture`, `store_connector` |
| `retention` | `core_inbox`, `contact_directory`, `business_settings`, `notification_triggers`, `ai_answers`, `campaign_segments` |
| `enterprise` | All above + `branch_routing` |

---

## 9. Demo Fixture Design (W1-091)

### Synthetic Tenants

| Field | Restaurant A | Spare Parts B |
|---|---|---|
| Slug | `restaurant-alpha` | `spare-parts-beta` |
| Industry | `restaurant` | `spare_parts` |
| Package | `order_desk` (trial) | `receptionist` (trial) |

### Users

| Email | system_role | Memberships |
|---|---|---|
| `operator@demo.local` | `platform_admin` | None (no implicit membership to any tenant) |
| `owner.a@demo.local` | null | Owner in Restaurant A |
| `owner.b@demo.local` | null | Owner in Spare Parts B |
| `shared@demo.local` | null | Manager in A, Agent in B |

- Restaurant A staff count: owner.a + shared = 2 active (within 3-seat `order_desk` limit)
- Spare Parts B staff count: owner.b + shared = 2 active (within 2-seat `receptionist` limit)

### Contacts

- Restaurant A: 5 contacts including Sinhala name (`දිනේෂ් ප්‍රනාන්දු`) and Tamil note (`வாடிக்கையாளர்`)
- Spare Parts B: 5 contacts including one with the same phone as a contact in A (cross-tenant, permitted)
- One contact in A shares phone with one in B → proves T25 cross-tenant allowed
- Test script attempts a duplicate within A → proves T25 rejection

**Idempotency:** Seed uses stable slug/email lookups. Re-running on existing fixtures is safe and does not reset passwords or overwrite user-edited data.

---

## 10. Frontend Implementation Plan (W1-070, W1-071)

### Route Structure

```
/login                          → LoginPage (public only)
/workspaces                     → WorkspacesPage (session required)
/admin/tenants                  → TenantsPage (platform_admin required)
/app/:tenantId/overview         → OverviewPage (active membership required)
/app/:tenantId/settings         → SettingsPage (active membership required)
/app/:tenantId/contacts         → ContactsPage (active membership required)
/app/:tenantId/team             → TeamPage (owner/manager required)
/app/:tenantId/plan             → PlanPage (owner/manager required)
/403                            → ForbiddenPage
/404                            → NotFoundPage
/suspended                      → SuspendedPage
```

### State Management Design

**AuthContext** — stores `{ user, csrfToken, isLoading }`:
- On mount: calls `GET /auth/me`
- On 401: redirects to `/login`
- CSRF token stored in React memory only — never `localStorage` or `sessionStorage`
- Axios interceptor injects `X-CSRF-Token` on all non-GET requests

**WorkspaceContext** — stores `activeTenantId`:
- On change: calls TanStack Query `queryClient.invalidateQueries({ queryKey: [prevTenantId] })`
- Cancels in-flight requests via `AbortController`
- Resets all active form states via context signal

**TanStack Query cache keys:** Always prefixed with `tenantId`:
```ts
['contacts', tenantId, page, search, statusFilter]
['settings', tenantId]
['subscription', tenantId]
```

**Late response guard:** Every `useEffect` that fetches checks if `tenantId` still matches at resolution time; discards stale results.

### Unavailable Features Display

Modules not yet implemented shown as greyed-out cards with clear labels:
- "Inbox — Available from Week 3"
- "AI Answers — Available from Week 6"
- "Orders — Available from Week 8"

No fake counters, mock data, or interactive placeholders.

### LKR Formatting

```ts
// Minor units → display
const formatLKR = (minorUnits: number) =>
  new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR' })
    .format(minorUnits / 100);
```

### Time Zone

- Business settings displayed in the tenant's configured IANA time zone
- UTC instants never presented using developer PC locale
- `Intl.DateTimeFormat` with `timeZone: settings.time_zone`

---

## 11. CLI Commands (W1-090)

All via `python -m app.cli` (or `docker exec <api> python -m app.cli`):

```powershell
# Apply migrations (uses MIGRATION_DATABASE_URL, not DATABASE_URL)
.\scripts\migrate.ps1

# Provision platform operator
python -m app.cli provision-operator --email operator@example.com

# Create staff user
python -m app.cli create-user --email staff@example.com

# Assign to tenant
python -m app.cli assign-membership --tenant-slug my-biz --email staff@example.com --role manager

# Deactivate membership
python -m app.cli deactivate-membership --tenant-slug my-biz --email staff@example.com

# Seed demo data (dev/test only; rejected if APP_ENV=production)
python -m app.cli seed-demo

# Schema/role diagnostic
python -m app.cli diagnose
```

All passwords via interactive `getpass` prompt — never in arguments or shell history.

---

## 12. Windows / Docker / PowerShell Commands (W1-011)

### Prerequisites
- Docker Desktop with WSL2 backend
- Node.js 22 LTS + pnpm 9
- Python 3.12 + uv
- Git

### First-Time Setup
```powershell
# Clone and enter repo
git clone <repo-url>
Set-Location whatsapp-business-platform

# Configure environment
Copy-Item .env.example .env
# Edit .env — set passwords and secrets

# Start containers
docker compose up -d --build

# Apply migrations
docker exec wbp-api python -m alembic upgrade head

# Provision first operator (interactive password prompt)
docker exec -it wbp-api python -m app.cli provision-operator --email admin@local.dev

# Seed demo data
docker exec wbp-api python -m app.cli seed-demo
```

### Daily Development
```powershell
docker compose up -d

# Logs
docker compose logs -f api

# Backend tests (real PostgreSQL)
docker exec wbp-api pytest tests/ -v

# Frontend unit tests
docker exec wbp-web pnpm test

# Browser smoke tests (local)
pnpm --filter frontend exec playwright test

# Lint / type check (backend)
docker exec wbp-api ruff check app/ tests/
docker exec wbp-api mypy app/

# Fresh migration replay
docker exec wbp-api python -m alembic downgrade base
docker exec wbp-api python -m alembic upgrade head
```

### Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API via Vite proxy | http://localhost:5173/api |
| API direct | http://localhost:8000/api |

> Database (5432) and Redis (6379) are NOT exposed to host by default. Bind to `127.0.0.1` only if debugging requires access.

---

## 13. CI Pipeline Design (W1-013)

```yaml
# .github/workflows/ci.yml — outline

on: [push, pull_request]

jobs:
  backend:
    services:
      postgres: { image: postgres:17-alpine }
      redis:    { image: redis:7.4-alpine }
    steps:
      - uv sync (from lockfile)
      - ruff check + ruff format --check
      - mypy app/
      - alembic upgrade head (ephemeral test DB)
      - pytest tests/ --cov=app

  frontend:
    steps:
      - pnpm install --frozen-lockfile
      - pnpm lint
      - pnpm type-check
      - pnpm test --run
      - pnpm build

  browser:
    needs: [backend, frontend]
    steps:
      - docker compose up -d
      - alembic upgrade head + seed-demo
      - playwright test
```

> CI uses real PostgreSQL — never SQLite. Isolation tests (T01, T02, T15–T18) run against real `app_runtime` role with RLS enforced.

---

## 14. Requirement → Test Mapping (Verification Matrix)

| Test ID | Scenario | File | Req IDs |
|---|---|---|---|
| T01 | Fresh migration + seed reproducibility | `tests/integration/test_migrations.py` | W1-010, W1-020 |
| T02 | Runtime role: no superuser/BYPASSRLS/ownership | `tests/integration/test_db_roles.py` | W1-030 |
| T03 | Password stored as Argon2id; not in responses | `tests/unit/test_auth_service.py` | W1-040 |
| T04 | Valid login: cookie set, CSRF returned, no localStorage | `tests/integration/test_auth.py` | W1-040 |
| T05 | Unknown email vs wrong password: same 401 shape | `tests/integration/test_auth.py` | W1-040 |
| T06 | Logout/disabled user/expired session: no access | `tests/integration/test_auth.py` | W1-040 |
| T07 | Idle + absolute expiry with injected clock | `tests/unit/test_session_expiry.py` | W1-040 |
| T08 | Missing/wrong CSRF or Origin on mutations | `tests/integration/test_csrf.py` | W1-041 |
| T09 | Login failure thresholds; Redis unavailable → 503 | `tests/integration/test_throttle.py` | W1-041 |
| T10 | Unauthenticated → 401; non-operator → 403 on admin | `tests/integration/test_permissions.py` | W1-042 |
| T11 | Operator without membership: no contact/settings access | `tests/integration/test_permissions.py` | W1-042 |
| T12 | Non-member tenant request → 403; no data leaked | `tests/integration/test_permissions.py` | W1-042 |
| T13 | A reads B contact ID under A route → 404; B unchanged | `tests/integration/test_tenant_isolation.py` | W1-031, W1-032 |
| T14 | A supplies B tenant_id in body → rejected | `tests/integration/test_tenant_isolation.py` | W1-031 |
| T15 | Raw SQL without context → no rows; insert fails | `tests/integration/test_rls.py` | W1-030, W1-031 |
| T16 | Raw SQL with A context, no WHERE → only A rows | `tests/integration/test_rls.py` | W1-030, W1-031 |
| T17 | Pooled connection reuse/rollback: no context leak | `tests/integration/test_rls.py` | W1-031, W1-032 |
| T18 | Parallel A/B requests: independent rows + audits | `tests/integration/test_rls.py` | W1-031, W1-032 |
| T19 | Manager in A / agent in B: role not carried across | `tests/integration/test_permissions.py` | W1-042 |
| T20 | Deactivation/suspension: existing session loses access | `tests/integration/test_permissions.py` | W1-042, W1-043 |
| T21 | Concurrent staff provisioning at seat limit | `tests/integration/test_memberships.py` | W1-043 |
| T22 | Immutable package version; unimplemented = unavailable | `tests/integration/test_plans.py` | W1-060, W1-061 |
| T23 | Tenant provisioning failure → no orphan | `tests/integration/test_tenancy.py` | W1-031, W1-043 |
| T24 | Contact CRUD: state/version/role rules enforced | `tests/integration/test_contacts.py` | W1-022 |
| T25 | Same phone A/B allowed; duplicate within A rejected | `tests/integration/test_contacts.py` | W1-022 |
| T26 | Stale version → 409; no overwrite or false audit | `tests/integration/test_contacts.py` | W1-051 |
| T27 | Invalid hours/timezone/email/phone/extra fields → 422 | `tests/unit/test_validators.py` | W1-051 |
| T28 | Search/pagination/Unicode: bounded, scoped, multilingual | `tests/integration/test_contacts.py` | W1-051 |
| T29 | Suspended account: own metadata visible; data blocked | `tests/integration/test_permissions.py` | W1-042 |
| T30 | Browser workspace switch with late response | `frontend/tests/workspace.spec.ts` | W1-071 |
| T31 | Health dependency failure → 503 readiness | `tests/integration/test_health.py` | W1-011 |
| T32 | Logs/errors/fixtures contain no secrets/tokens | `tests/unit/test_logging.py` | W1-080 |
| T33 | Full browser journey: login→A→settings→contacts→B→logout | `frontend/tests/e2e/journey.spec.ts` | W1-070 |

---

## 15. Day-by-Day Execution Order

| Day | Work slice | Evidence |
|---|---|---|
| **1** | Review proposal → repo scaffold: `.gitignore`, `compose.yaml`, `pyproject.toml`, `package.json`, `Dockerfile`s, `.env.example`, CI skeleton | `docker compose up -d` works; `/api/health/live` returns 200 |
| **2** | Alembic migration `0001`: all tables, roles, grants, RLS policies, package seed | T01, T02, T15, T16 pass against real PostgreSQL as `app_runtime` role |
| **3** | Auth module: login, session, CSRF, throttle, logout, me, dummy hash, injected clock | T03–T09 pass |
| **4** | Tenancy + plans + contacts modules; admin routes; atomic provisioning; CRUD; audit | T10–T29 pass |
| **5** | React: login, workspace selector, admin panel, app shell, settings, contacts, team, plan | Browser flows use real API; T30 implemented |
| **6** | Concurrency tests (T21, T18, T17); Playwright smoke (T33); migration replay; CI green | All 33 tests verified; CI passes on clean checkout |
| **7** | Founder walkthrough; README, AGENTS.md, 3 ADRs, completion report; fix failures | Acceptance matrix complete; gaps listed honestly |

---

## 16. Configuration Variables (W1-012)

`.env.example` (placeholders only — no usable credentials):

```bash
# Application
APP_ENV=development
APP_LABEL=whatsapp-business-platform
API_PREFIX=/api/v1
ALLOWED_ORIGINS=http://localhost:5173

# Database (application runtime role)
DATABASE_URL=postgresql+psycopg://app_runtime:CHANGEME@db:5432/wbp_dev

# Database (migration role — Alembic only, not used by application)
MIGRATION_DATABASE_URL=postgresql+psycopg://migration_owner:CHANGEME@db:5432/wbp_dev

# Redis
REDIS_URL=redis://redis:6379/0

# Session settings
SESSION_COOKIE_NAME=session
SESSION_IDLE_MINUTES=30
SESSION_ABSOLUTE_HOURS=12
SESSION_SECRET_KEY=CHANGEME-at-least-32-random-bytes

# Login throttling
THROTTLE_MAX_EMAIL_ATTEMPTS=5
THROTTLE_MAX_IP_ATTEMPTS=20
THROTTLE_WINDOW_MINUTES=15
THROTTLE_PSEUDONYM_SECRET=CHANGEME-separate-secret

# Test database (separate DB — never points to production)
TEST_DATABASE_URL=postgresql+psycopg://app_runtime:CHANGEME@db:5432/wbp_test
```

**Production enforcement:**
- `APP_ENV=production` → Secure cookie flag required; no seed route; HTTPS-only CORS
- Missing required variables → startup validation failure with clear message
- Runtime never receives `MIGRATION_DATABASE_URL`

---

## 17. Architectural Decisions Summary

### Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| Backend package manager | `uv` | Fastest resolver; deterministic `uv.lock`; single binary |
| Frontend package manager | `pnpm` | Strict isolation; fast; deterministic lockfile |
| PostgreSQL driver | `psycopg` v3 (async) | Best SQLAlchemy 2.0 integration; typed parameters |
| Time zone library | stdlib `zoneinfo` | Python 3.12 standard; `tzdata` package for Windows |
| Password hashing | Argon2id via `argon2-cffi` | OWASP current recommendation; memory-hard |
| Frontend state | TanStack Query | Best cache invalidation control for workspace switching |

### Assumptions

1. Founder will review and approve this plan before any implementation begins.
2. Docker Desktop with WSL2 is installed on the development Windows machine.
3. A single Alembic migration covers all Week 1 schema; new migrations added if needed mid-week.
4. `pnpm` is the chosen Node package manager.

### Deviations from Spec

None. All requirements W1-001 through W1-101 are addressed above.

### Risks

| Risk | Mitigation |
|---|---|
| Docker networking inconsistency on Windows | Explicit container names; loopback-only port binds |
| Playwright flakiness on Windows | Docker-based Playwright runner in CI |
| RLS context leakage across pooled connections | T17 specifically tests commit/rollback context isolation |
| Unicode collation differences across PG instances | T28 seeds Sinhala/Tamil content; migration sets locale explicitly |
| Argon2id memory on low-RAM dev machine | Document minimum parameters; allow config override |

---

## 18. Paid Expenditure Confirmation

**Week 1 incurs zero paid external API costs:**

- ✅ No OpenAI API calls (AI module not yet implemented)
- ✅ No Meta/WhatsApp API calls (WhatsApp module not yet implemented)
- ✅ No production hosting required (all local Docker)
- ✅ No paid third-party service accounts needed

All software used (PostgreSQL, Redis, Python, React, Docker, GitHub Actions free tier) is open source or free for the described usage.

---

## 19. Questions Requiring Founder Decision Before Implementation

| # | Question | Default if not answered |
|---|---|---|
| 1 | Package managers: `uv` + `pnpm` acceptable? | Proceed with `uv` + `pnpm` |
| 2 | Should DB (5432) and Redis (6379) be exposed to host for debugging? | Not exposed by default |
| 3 | Reserved slugs: add any beyond `admin`, `api`, `auth`, `app`, `health`? | Use proposed list |
| 4 | CI platform: GitHub Actions, or another? | GitHub Actions assumed |
| 5 | Playwright: run in Docker (CI) only, or install locally too? | Docker for CI; local optional |
| 6 | Opening hours UI hint for overnight: show explicit label? | Yes, show guidance text |

---

*This document covers all requirements W1-001 through W1-101. No application code has been implemented. Awaiting founder review and approval before Day 1 implementation begins.*
