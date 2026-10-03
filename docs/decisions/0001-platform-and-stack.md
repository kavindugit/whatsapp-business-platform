# ADR 0001: Platform and Stack Selection

## Context
We are building a multi-tenant WhatsApp Business Automation Platform. The system needs to support high concurrency for webhook events (WhatsApp messages), robust background processing, strict data isolation, and a responsive frontend for workspace management.

## Decision
We have selected the following core stack for Week 1 and beyond:
1. **Backend Framework**: FastAPI (Python 3.12). FastAPI provides excellent async support, auto-generated OpenAPI documentation, and high performance via Starlette and Pydantic.
2. **Database**: PostgreSQL 17 with `psycopg` v3 driver. PostgreSQL offers robust Row-Level Security (RLS) necessary for our tenant isolation model, and JSONB for flexible schema parts (like feature permissions).
3. **ORM**: SQLAlchemy 2.0 with async engine. Selected for its maturity and explicit async control.
4. **Frontend Framework**: React 19 + TypeScript + Vite. 
5. **State Management**: TanStack Query (React Query) for server state caching and optimistic updates, strictly keyed by `tenantId`.
6. **Package Management**: `uv` for Python (fast, deterministic locking) and `pnpm` for Node.js.

## Rationale
- **FastAPI + Async**: WhatsApp webhooks require high concurrency. Async Python is well-suited for I/O bound tasks.
- **PostgreSQL RLS**: Moving tenant isolation to the database layer reduces the risk of application-level data leaks.
- **TanStack Query**: Essential for a multi-tenant frontend where switching workspaces must instantly invalidate and scope cache contexts.

## Consequences
- Developers must be familiar with async Python and SQLAlchemy 2.0 paradigms.
- Frontend developers must strictly adhere to prefixing all query keys with the active `tenantId`.
- Database migrations require careful handling of RLS policies for every new tenant-owned table.
