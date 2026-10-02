# WhatsApp Business Automation Platform

A multi-tenant SaaS platform that lets independent businesses handle WhatsApp enquiries, staff handovers, orders, bookings and updates via the official WhatsApp Business Cloud API.

**Current state: Week 1 — Platform Foundation.** This is not yet a live bot or saleable package.

---

## Week 1 Scope

What is implemented this week:
- Repository structure, local Docker stack, configuration and CI
- Staff authentication with server-side sessions (no localStorage tokens)
- Multi-tenant workspaces with PostgreSQL row-level security isolation
- Platform operator and tenant role-based access control
- Business workspace settings and contact directory
- Ten package catalogue definitions (all `planned` — not yet saleable)
- Audit records for all meaningful mutations

What is **not** implemented (outside Week 1):
- WhatsApp webhooks or live messaging
- OpenAI / AI features
- Orders, bookings, campaigns, payments, external calendar connections
- Production deployment

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with WSL2 backend
- [Node.js 22 LTS](https://nodejs.org/) + [pnpm 9](https://pnpm.io/installation)
- [Python 3.12](https://www.python.org/downloads/) + [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Git](https://git-scm.com/)

---

## First-time setup

```powershell
# 1. Clone the repository
git clone <repo-url>
Set-Location whatsapp-business-platform

# 2. Copy and configure environment variables
Copy-Item .env.example .env
# Open .env and replace all CHANGEME values with real secrets
# Generate secrets: python -c "import secrets; print(secrets.token_hex(32))"

# 3. Start all containers (builds images on first run)
docker compose up -d --build

# 4. Wait for containers to be healthy, then apply migrations
docker exec wbp-api python -m alembic upgrade head

# 5. Provision the first platform operator
docker exec -it wbp-api python -m app.cli provision-operator --email admin@local.dev

# 6. (Optional) Seed synthetic demo data
docker exec wbp-api python -m app.cli seed-demo
```

---

## Local URLs

| Service | URL |
|---|---|
| **Frontend dashboard** | http://localhost:5173 |
| **API health** | http://localhost:5173/api/health/live |
| **API readiness** | http://localhost:5173/api/health/ready |
| **API docs (dev only)** | http://localhost:5173/api/docs |

Database and Redis are **not** exposed to the host by default (internal Docker network only).

---

## Daily development

```powershell
# Start containers
docker compose up -d

# View logs
docker compose logs -f api
docker compose logs -f web

# Stop containers
docker compose down
```

---

## Running tests

### Backend tests (real PostgreSQL — required for isolation tests)

```powershell
# All tests
docker exec wbp-api pytest tests/ -v

# With coverage
docker exec wbp-api pytest tests/ --cov=app --cov-report=term-missing

# Specific test file
docker exec wbp-api pytest tests/integration/test_rls.py -v
```

### Frontend unit tests

```powershell
docker exec wbp-web pnpm test
# Or locally (requires Node.js + pnpm installed):
Set-Location frontend
pnpm test
```

### Browser smoke tests (Playwright)

```powershell
# Requires local Playwright installation:
Set-Location frontend
pnpm exec playwright install --with-deps chromium
pnpm e2e
```

### Lint and type checks

```powershell
# Backend
docker exec wbp-api ruff check app/ tests/
docker exec wbp-api mypy app/

# Frontend
docker exec wbp-web pnpm lint
docker exec wbp-web pnpm type-check
```

---

## CLI commands

All commands run inside the API container (or locally with Python 3.12 + uv installed):

```powershell
# Apply database migrations (uses migration_owner role)
docker exec wbp-api python -m alembic upgrade head

# Downgrade all migrations (careful — destroys schema)
docker exec wbp-api python -m alembic downgrade base

# Provision platform operator (interactive password prompt)
docker exec -it wbp-api python -m app.cli provision-operator --email admin@example.com

# Create a staff user
docker exec -it wbp-api python -m app.cli create-user --email staff@example.com

# Assign staff to a workspace
docker exec wbp-api python -m app.cli assign-membership \
  --tenant-slug my-business --email staff@example.com --role manager

# Deactivate a membership
docker exec wbp-api python -m app.cli deactivate-membership \
  --tenant-slug my-business --email staff@example.com

# Seed demo data (development/test only)
docker exec wbp-api python -m app.cli seed-demo

# Show schema and role diagnostic
docker exec wbp-api python -m app.cli diagnose
```

**Security:** Passwords are never supplied as command-line arguments. Use the interactive prompt.

---

## Migration management

```powershell
# Show current migration state
docker exec wbp-api python -m alembic current

# Show migration history
docker exec wbp-api python -m alembic history

# Fresh replay (for testing reproducibility)
docker exec wbp-api python -m alembic downgrade base
docker exec wbp-api python -m alembic upgrade head
```

> ⚠️ The application never runs migrations automatically on startup. Run them explicitly.

---

## Configuration

All configuration is set through environment variables. See [`.env.example`](.env.example) for full documentation.

**Required variables:**
- `DATABASE_URL` — PostgreSQL connection string for the `app_runtime` role
- `MIGRATION_DATABASE_URL` — PostgreSQL connection string for the `migration_owner` role (Alembic only)
- `SESSION_SECRET_KEY` — At least 32 random bytes
- `THROTTLE_PSEUDONYM_SECRET` — Separate secret for pseudonymising throttle keys

**Never commit `.env` to the repository.**

---

## Architecture

See [`docs/PROJECT_BLUEPRINT.md`](docs/PROJECT_BLUEPRINT.md) for full architecture documentation.

Key design principles:
- **Tenant isolation:** Every tenant-owned table has `tenant_id` + PostgreSQL RLS. The application role (`app_runtime`) has no `BYPASSRLS` privilege.
- **Session security:** HttpOnly cookies; sessions stored server-side in PostgreSQL; no tokens in localStorage.
- **CSRF protection:** X-CSRF-Token header required on all state-changing requests.
- **AI deferred:** OpenAI integration begins in Week 6. No AI credentials required this week.

---

## Project structure

```
whatsapp-business-platform/
├── backend/          Python FastAPI application
│   ├── app/
│   │   ├── core/     Config, clock, errors, logging, security
│   │   ├── db/       Models, session, tenant context
│   │   └── modules/  auth, tenancy, plans, contacts, audit
│   ├── migrations/   Alembic schema migrations
│   └── tests/        Unit and integration tests
├── frontend/         React TypeScript dashboard
│   └── src/
│       ├── app/      Router and context providers
│       ├── api/      Typed HTTP client
│       ├── components/ Shared UI components
│       └── features/  Page-level feature modules
├── docs/             Architecture, decisions, plans, reports
└── scripts/          Database init and helper scripts
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `docker compose up` fails with port conflict | Check if ports 5173 or 8000 are in use: `netstat -ano \| findstr :5173` |
| API container crashes on startup | Check `.env` has all required variables; run `docker compose logs api` |
| "Session SECRET_KEY too short" error | Regenerate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| Migrations fail with "role does not exist" | Ensure the DB container initialised; check `docker compose logs db` |
| Frontend shows "failed to fetch" | API container may not be ready; check `/api/health/ready` |

---

## Known limitations (Week 1)

- No WhatsApp connection, messaging, or real-time features
- No AI or OpenAI integration
- No payment collection or invoice generation
- No production deployment — local development only
- All packages have `planned` status; none are saleable
- Usage counters display "Not available yet"
- Staff provisioning is CLI-only (no invite emails yet)

---

## Roadmap

See [`docs/PROJECT_BLUEPRINT.md`](docs/PROJECT_BLUEPRINT.md) §10 for the 12-week roadmap. Week 2 begins only after Week 1 acceptance criteria are fully met.