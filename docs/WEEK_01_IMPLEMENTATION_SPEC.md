# Week 1 — Platform Foundation and Tenant Isolation

Version: 1.0 | Prepared: 2026-10-01 | Companion: `PROJECT_BLUEPRINT.md`

This is a requirements specification for a coding agent, not application code. Produce an implementation proposal first. The founder will review it, possibly with this assistant, before asking the coding agent to implement. Implement Week 1 only. Later weeks will be specified after reviewing completed work.

## 1. Week 1 outcome

At the end of Week 1, the founder can run the platform locally, sign in, create a business workspace, provision its owner, select an authorised workspace, view its package, change its business settings and manage its contact directory. A second business cannot see or alter the first business's data. Both application checks and real PostgreSQL row-security tests demonstrate this.

This is the foundation for the future WhatsApp bot. It is not yet a live bot or saleable package.

Estimated effort: 35–45 focused founder hours, including reviewing coding-agent output and fixing failures. If this takes longer, complete the gate before moving to Week 2. Coding assistance does not remove review or external approval work.

### W1-001: In scope

- Reproducible repository, local containers, configuration, migrations, lint/type checks and CI.
- Staff authentication using revocable server-side sessions.
- Platform operator, tenant memberships and role-based route permissions.
- Business workspace creation, suspension, settings and contact CRUD.
- Ten proposed package definitions, immutable version snapshots, subscription metadata and feature availability distinctions.
- Audit records for meaningful mutations and secure structured error handling.
- Minimal working React dashboard with real API data and clear unavailable-feature states.
- Deterministic synthetic demo fixtures and outcome-based tests using PostgreSQL.
- Development documentation, decision records, a completion report and a review bundle.

### W1-002: Explicitly outside Week 1

Do not implement WhatsApp APIs/webhooks, real messages, OpenAI calls, document ingestion, orders, bookings, campaigns, payment collection, real-time sockets, external calendars or production deployment. Do not create dummy endpoints that report those actions as successful. No customer data is required.

External provider setup is a founder preparation task, not a reason to hold up local development. Record Meta onboarding status without claiming approval.

## 2. Proposal required before implementation

Create `docs/plans/week-01-proposed-implementation.md` in the target project. Include:

1. Existing repository inventory and whether it is empty; any files that must be preserved.
2. Selected supported runtime/library versions, package manager and lockfile strategy.
3. Planned file tree, migrations, database roles and transaction/session design.
4. Requirement IDs mapped to implementation slices and tests.
5. Exact local commands for the founder's Windows/PowerShell environment and Docker workflow.
6. Authentication/CSRF design, tenant checks and row-security policy details.
7. Risks, ambiguities and proposed deviations. State assumptions explicitly.
8. Expected paid commitments: Week 1 should have none beyond already owned development tools.

Do not start application implementation until the founder asks you to proceed after this proposal. This pause comes from the founder's requested review workflow.

## 3. Day-by-day execution order

These are work slices, not deadlines that justify skipping unfinished tests.

| Day | Work slice | Evidence |
|---:|---|---|
| 1 | Proposal/review, repository, dependencies, Compose, configuration, CI skeleton | Fresh-start commands work; backend/web liveness available |
| 2 | Schema, role grants, migrations, package seed and tenant transaction helper | Real PostgreSQL isolation tests pass |
| 3 | Staff sessions, CSRF, login throttling, membership/role checks | Authentication and denied-access tests pass |
| 4 | Admin workspace routes, owner provisioning, settings, contacts and audit | Two tenants complete isolated CRUD flows |
| 5 | React login, workspace selection, dashboards, forms and lists | Browser flows use real API data |
| 6 | Boundary/concurrency tests, frontend checks, clean migration replay, documentation | CI and fresh-database verification pass |
| 7 | Founder walkthrough, fixes and review bundle | Acceptance matrix complete; gaps remain visible |

## 4. Repository and local environment

### W1-010: Required structure

Suggested repository name: `whatsapp-business-platform`; final product branding can change without renaming code per customer.

```text
whatsapp-business-platform/
  README.md
  AGENTS.md
  .gitignore
  .env.example
  compose.yaml
  backend/
    pyproject.toml
    <committed dependency lockfile>
    Dockerfile
    alembic.ini
    migrations/
    app/
      main.py
      cli.py
      core/                 # config, clock, errors, logging, security
      db/                   # models, sessions, tenant transaction helper
      modules/
        auth/
        tenancy/
        plans/
        contacts/
        audit/
    tests/
      unit/
      integration/
  frontend/
    package.json
    <committed dependency lockfile>
    Dockerfile
    src/
      app/                  # routing, auth context, workspace context
      api/                  # typed client, errors
      components/
      features/
        auth/
        tenants/
        settings/
        contacts/
        plans/
    tests/
  docs/
    PROJECT_BLUEPRINT.md
    WEEK_01_IMPLEMENTATION_SPEC.md
    plans/
    decisions/
    reports/
  scripts/
  .github/workflows/         # if GitHub is used
```

Keep handler, validation schema, service and persistence responsibilities separated. Avoid generic repositories that bypass tenant context or a single huge route file. Do not scaffold future business modules with invented implementations.

### W1-011: Local services

- Compose: PostgreSQL, Redis, API and web. A Celery worker is not required until Week 2.
- Web served on `http://localhost:5173`; Vite proxies `/api` to the API container.
- API listens inside its container; optional host debugging binds to loopback only.
- Database/Redis ports need not be published. If debugging requires them, bind to loopback, never all network interfaces.
- Docker named volume for PostgreSQL data. Redis for login throttling; loss of Redis must not erase business records or staff sessions.
- Health checks and dependency start conditions. Document that container startup does not prove migrations are applied.
- Explicit migration command; do not run destructive migration resets on application startup.
- Reproducible Windows instructions through Docker Desktop/WSL2. Avoid requiring `make`; offer a PowerShell-friendly path.
- Build scripts must use proper file paths, not assumptions about a user's drive letters.

### W1-012: Configuration

At minimum, document `APP_ENV`, application label, API prefix, allowed browser origins, runtime database URL, separate migration database URL, Redis URL, session settings, login-throttle settings and a secret used to pseudonymise throttle/log identifiers.

- `.env.example` contains placeholders and non-secret defaults, not usable shared production credentials.
- Production configuration requires HTTPS session cookies and rejects development seed mode.
- Configuration validation fails clearly for missing/invalid required values.
- Runtime does not receive migration credentials. One-off migration tooling may receive them through a separate profile/command.
- No OpenAI or Meta keys are required or transmitted in Week 1.
- Ignore `.env`, private keys, database dumps, uploads, browser auth-state files and generated local reports containing secrets.
- Use separate development and test databases. Test/reset commands refuse a non-test target; production has no demo/reset route.

### W1-013: Build tooling

- Backend: locked dependencies, Ruff lint/format, a consistent Python type checker and pytest.
- Frontend: TypeScript strict mode, ESLint, consistent formatting, Vitest/React Testing Library and a production build.
- Browser smoke tests: Playwright for the meaningful login/tenant/CRUD journey.
- CI: install from lockfiles, migrate a disposable real PostgreSQL database, run backend tests, frontend checks/tests/build and the browser smoke journey.
- Never use SQLite as the tenant-isolation test substitute.

## 5. Data model

### W1-020: Shared conventions

- UUID primary keys; UTC timezone-aware timestamps; server-generated audit timestamps.
- Field limits validated by Pydantic and appropriate database constraints. Reject unknown request fields.
- Money in integer minor units: LKR 6,900.00 is `690000` minor units; currency explicitly `LKR`. No binary floating-point financial calculations.
- Business-local times are not confused with UTC instants. Store an IANA time-zone identifier.
- Where a child references a tenant-owned parent, use a composite foreign key `(tenant_id, parent_id)` to a corresponding unique parent key. A global UUID foreign key alone does not prevent cross-tenant relationships.
- Do not build all future domain tables now. Document their intended ownership only.

### W1-021: Control-plane tables

These are accessed only by explicit authentication/administration services. They contain sensitive metadata and must not be exposed through generic list endpoints.

| Table | Minimum fields and rules |
|---|---|
| `users` | `id`, canonical unique email, `display_name`, Argon2id password hash, `status` (`active`/`disabled`), `system_role` (`platform_admin` or null), timestamps. No passwords returned in DTOs. |
| `auth_sessions` | `id`, `user_id`, unique SHA-256 hash of random session token, CSRF token, created/last-seen/absolute-expiry times, revoked time. Never store raw session tokens. CSRF value is not an authentication credential and must still not be logged. |
| `tenants` | `id`, unique normalised slug, `display_name`, optional `legal_name`, industry tag, status (`active`/`suspended`), optimistic `version`, timestamps. Slug changes are deferred. |
| `tenant_memberships` | `id`, `tenant_id`, `user_id`, role (`owner`/`manager`/`agent`), status (`active`/`inactive`), timestamps; unique `(tenant_id,user_id)`. One owner initially; ownership transfer is deferred. |
| `packages` | Stable unique code, name, mutable release status (`planned`/`internal`/`pilot`/`saleable`), description. Week 1: all packages `planned`. |
| `package_versions` | Package ID, version integer, currency, monthly/setup prices in minor units, staff/number limits, validated feature permissions and metric limits, created timestamp; immutable after creation. |
| `subscriptions` | One current row per tenant: plan-version reference, status (`trial`/`active`/`past_due`/`suspended`/`cancelled`), period start/end, retained anniversary anchor, timestamps. Plan history/renewal engine comes later. No payment settlement claims. |
| `platform_audit_events` | Actor, action, target tenant/user identifier, request ID and safe metadata; operator mutations and membership administration. Append only through services. |

Week 1 subscriptions are synthetic internal trials, not paid activations. Production activation of an unreleased package must be disallowed. Do not silently mutate a package version assigned to customers.

Owner/manager permissions apply within memberships; `system_role` cannot be supplied or changed through tenant settings or normal user updates.

### W1-022: Tenant-owned tables — row-security required

| Table | Minimum fields and rules |
|---|---|
| `business_settings` | `tenant_id` primary key/FK, public business name, optional public email/phone, address text, time zone (default `Asia/Colombo`), currency (`LKR` initially), preferred reply language (`auto`/`en`/`si`/`ta`), requested languages, opening-hours JSON, escalation text, optimistic `version`, timestamps. |
| `contacts` | `id`, `tenant_id`, `display_name`, optional normalised `phone_e164`, optional email, optional preferred language, notes, status (`active`/`archived`), optimistic `version`, timestamps. Partial unique non-null phone among active contacts within a tenant; same phone allowed in another tenant. Unique `(tenant_id,id)` for future composite references. |
| `tenant_audit_events` | `id`, `tenant_id`, actor ID, action, target type/ID, request ID, safe changed-field metadata, created timestamp. Tenant-scoped, append-only service access. |

Do not require telephone numbers for every contact. Future WhatsApp messaging identity is a separate channel identity table containing the provider sender identifier and business connection. Manual contacts are not proof of WhatsApp consent or account ownership.

Suggested limits: names 120 characters, notes/address/escalation text 1,000, business description 2,000 where used. An email validator and telephone normalisation utility must be tested. Empty optional values become null consistently. Do not silently assume a country when a number is ambiguous; ask for international format in Week 1.

Opening hours: seven weekday entries, each with zero to four non-overlapping `{start:'HH:mm',end:'HH:mm'}` intervals. Empty means closed. Require `start < end`. Overnight operation uses two intervals split across adjacent days; describe this in the UI. Holiday/resource scheduling is deferred.

## 6. Database access and isolation

### W1-030: Roles and grants

- Separate `migration_owner` and `app_runtime` roles. Password values come from local configuration, not committed SQL.
- `app_runtime`: non-superuser, no `BYPASSRLS`, not a member of the owner role, no schema/role creation and no table ownership.
- Grant only required control-table operations and tenant-table operations. Runtime cannot disable RLS, truncate tables or write package-version definitions.
- Package seeds execute as explicit migration/seed tooling. Subscription/account creation uses authorised application services.
- Test the actual runtime role properties and table ownership, not just role names.
- Enable and force row-level security on every W1-022 table. Owner/migration behaviour must not be confused with runtime isolation.

### W1-031: Transaction context contract

Create one reusable helper, conceptually `tenant_transaction(validated_context)`, that:

1. Receives a context built by the server after authentication/membership validation, or an explicitly authorised provisioning operation.
2. Checks out a runtime connection and starts one transaction.
3. Sets the transaction-local setting with a bound parameter: `SELECT set_config('app.tenant_id', :tenant_id, true)`.
4. Executes all scoped reads, writes and tenant audits in that transaction on that connection.
5. Commits only on success; rolls back on failures; returns the connection safely.

Policies must constrain both reads and written values to `tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`. Missing/empty context denies rows. Context inputs must be valid UUIDs before setting the value. This is a policy expression pattern, not permission to concatenate untrusted SQL.

- Use explicit `USING` and `WITH CHECK` policies appropriate to the commands/role.
- Every service creates tenant-owned rows using the validated context. Do not accept `tenant_id` from a contact/settings request body.
- Application queries also constrain the tenant for clarity and indexes; RLS catches forgotten filtering.
- Read/edit contacts by `(tenant_id,id)`. A foreign tenant's object returns 404 after workspace authorisation, not identifying data.
- Runtime control-table access is not protected by these policies. Authentication selects only the exact session/user and requested membership; admin listing requires the operator role.
- Provision tenant metadata, subscription, initial owner membership when supplied, settings and audits atomically in one database transaction. Set trusted context to the newly server-generated tenant UUID before scoped writes.
- No global switch such as `disable_tenant_checks`, `is_admin_bypass` or an optional arbitrary tenant override.

### W1-032: Isolation acceptance

Required direct-database tests as runtime role: missing-context reads return no tenant rows; missing-context writes fail; A context sees only A even for an intentionally unfiltered query; A cannot insert B rows or move A rows to B; switching A/B across reused pooled connections never leaks; rollback clears context; parallel A/B requests remain isolated.

A settings-write failure during provisioning must roll back the tenant and subscription too. No leftover partially created workspace.

## 7. Authentication and authorisation

### W1-040: Login/session contract

- Dashboard staff only; no WhatsApp end-user signup endpoint.
- Provision the first platform operator via an explicit CLI command and hidden password prompt.
- Hash passwords with Argon2id using a maintained library; no homemade hashing.
- Proposed password rule for provisioned staff: 12–128 characters, permit spaces, do not trim passwords, and avoid composition rules that force a particular symbol. Record chosen parameters.
- Login accepts JSON email/password. Trim/canonicalise email, not password. Wrong email/password gives the same 401 response and similar handling, including a dummy hash check for absent users.
- Session token: at least 256 random bits from a cryptographic generator, hashed at rest and rotated on login.
- Cookie: HttpOnly, `SameSite=Lax`, path `/`, host-only. Secure in HTTPS environments. A development-only localhost cookie may lack Secure; never make this a general production toggle.
- Idle expiry: 30 minutes. Absolute expiry: 12 hours. Enforce on the server using an injectable clock. Do not let idle refresh exceed absolute expiry.
- Logout revokes the session server-side and expires the cookie. Disabled users cannot keep using an existing session.
- Auth responses use `Cache-Control: no-store`. Frontend stores neither passwords nor authentication tokens in localStorage/sessionStorage.
- Read membership and role state from the database for each protected tenant request; removing membership takes effect without waiting for cookie expiry.

### W1-041: CSRF and login throttling

- Same-origin frontend/API in production. Local browser requests pass through Vite's `/api` proxy.
- Every state-changing browser request validates its Origin against an explicit allowlist; browser clients do not gain trust from Host or an arbitrary forwarded header.
- Authenticated unsafe methods also require `X-CSRF-Token`, checked against the current session using constant-time comparison.
- Return the session's CSRF token through login and `/auth/me` so a refresh can restore it into frontend memory. Never treat it as the session credential.
- Login has no authenticated CSRF token yet: require JSON and an allowed Origin; reject form/simple requests. Logout requires CSRF.
- Cross-origin credentialed access is denied unless explicitly reviewed. No wildcard credentialed CORS.
- Throttle using shared Redis counters: default five failed attempts per canonical email and twenty per source IP per 15 minutes. Store pseudonymised email keys. Define when 429 begins and test boundary/reset behaviour with a clock or controlled TTLs.
- Do not trust caller-supplied `X-Forwarded-For`. Only a configured trusted reverse proxy may supply the client IP.
- When Redis cannot enforce login throttling, new logins fail with a clear 503; existing DB-backed sessions can continue if other dependencies work. No fail-open brute-force protection.

### W1-042: Role matrix

| Operation | Platform admin without membership | Owner | Manager | Agent |
|---|---:|---:|---:|---:|
| List/create/suspend tenant metadata | Yes | No | No | No |
| View own workspace settings | No | Yes | Yes | Yes |
| Edit workspace settings | No | Yes | Yes | No |
| Read/create/update contacts | No | Yes | Yes | Yes |
| Archive/restore contacts | No | Yes | Yes | No |
| Read subscription/limits | Admin metadata route only | Yes | Yes | No |
| List workspace staff | No | Yes | Yes | No |
| Change owner/system role | No normal tenant route | Deferred | No | No |

CLI staff provisioning is operator-controlled, not a public API. If an operator also has an explicit membership, tenant actions use that membership's permissions, not an implicit operator bypass.

Tenant suspension blocks tenant-data operations. Login, `/auth/me`, own workspace selection and logout still work to show account status. Admin can inspect metadata and reactivate; the tenant route must not bypass suspension.

### W1-043: Membership provisioning and staff limits

- CLI can create a staff identity, add an existing identity to a workspace and deactivate membership. It reuses services and records operator audits.
- Include the owner in the active staff limit; one identity with multiple memberships counts once in each workspace.
- Lock the appropriate tenant/subscription row when adding/reactivating staff so concurrent operations cannot exceed the plan limit.
- Inactive memberships do not consume active seats. Deactivation takes effect on the next request.
- Owner creation/membership assignment within workspace provisioning must be atomic where requested.
- Enforce at most one active owner with a database constraint. A newly created workspace without an owner is visibly pending provisioning; it cannot be onboarded to a live channel later until owner assignment completes.
- No owner removal without a replacement-owner procedure; transfer is not implemented this week.
- Do not add platform operators as counted members to every tenant merely to gain access.

## 8. API contract

### W1-050: Required endpoints

Prefix: `/api/v1`. Health URLs may live under `/api` to work through the proxy. Exact naming adjustments require an updated contract, not mismatched frontend/backends.

| Method/path | Auth and behaviour |
|---|---|
| `GET /api/health/live` | Process liveness only; no secrets or database details |
| `GET /api/health/ready` | Required schema/database and Redis reachable; 503 on failure; bounded dependency checks |
| `POST /auth/login` | Origin/JSON validation, throttling, session cookie, safe user summary and CSRF token |
| `POST /auth/logout` | Session/CSRF; revoke and clear cookie |
| `GET /auth/me` | User summary, own active memberships, tenant statuses, own system role and CSRF token; no other users' records |
| `GET /admin/tenants` | Operator only; paginated metadata, package/status summaries; no contacts |
| `POST /admin/tenants` | Operator only; create name/slug/industry, trial plan and initial settings; optional existing owner-user reference validated server-side |
| `PATCH /admin/tenants/{tenant_id}/status` | Operator only; active/suspended with reason, optimistic version/check; audit |
| `GET /admin/tenants/{tenant_id}` | Operator metadata and provisioning status; no customer contact/settings-content shortcut |
| `GET /packages` | Authenticated catalogue, price/limits and planned availability; no checkout or activation claim |
| `GET /tenants/{tenant_id}/settings` | Valid active membership and tenant; settings DTO/version |
| `PATCH /tenants/{tenant_id}/settings` | Owner/manager; allowlisted fields and expected version; validation/audit |
| `GET /tenants/{tenant_id}/members` | Owner/manager; staff summary/role/status; no hashes/session details |
| `GET /tenants/{tenant_id}/subscription` | Owner/manager; assigned version, trial/status and configured limits; usage is explicitly unavailable this week |
| `GET /tenants/{tenant_id}/contacts` | Membership; bounded pagination/search and active/archived status filter |
| `POST /tenants/{tenant_id}/contacts` | Membership; validated fields, tenant supplied by context, 201 |
| `GET /tenants/{tenant_id}/contacts/{contact_id}` | Membership; own record or 404 |
| `PATCH /tenants/{tenant_id}/contacts/{contact_id}` | Membership; allowlisted contact fields/expected version, own record only |
| `POST /tenants/{tenant_id}/contacts/{contact_id}/archive` | Owner/manager, expected version, safe repeated state handling |
| `POST /tenants/{tenant_id}/contacts/{contact_id}/restore` | Owner/manager, expected version, unique-phone conflict handling |

No hard-delete contact endpoint in Week 1. Data deletion/export policy is a later explicit workflow; archive is not a claim of legal deletion.

### W1-051: Validation and response rules

- Tenant UUID route requests must be authorised before object access. Non-member tenant request: generic 403; own tenant with foreign object UUID: 404.
- Invalid UUID/field inputs: 422 in the common error format. Forbidden fields, including `tenant_id`, `system_role`, package permissions and timestamps, are rejected.
- Duplicate slug/own contact phone: 409 with safe field code; never echo another tenant's data.
- Slugs: normalised lowercase, 3–63 characters, letters/digits separated by single hyphens; reserve routing names such as `admin`, `api` and `auth`.
- Contact PATCH permits name, phone, email, preferred language and notes only. Archive status is changed only through the role-checked archive/restore routes, not by an agent supplying `status` in PATCH.
- Mutation bodies contain `expected_version`; a stale version returns 409 `VERSION_CONFLICT`. Increment version only after successful change.
- Lists default 25, maximum 100; validate non-negative offset or a documented cursor. Stable ordering uses timestamp plus UUID. Include total/next-page metadata without cross-tenant counts.
- Contact search is capped in length, parameterised and tenant-scoped; simple name/phone/email matching is enough. No arbitrary SQL query parameters.
- Opening hours, IANA time zone, email, phone, role and plan code are validated.
- Business settings language choices are requested configuration, not proof of tested AI language quality.

Common error envelope:

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

Document 400/401/403/404/409/422/429/503 behaviour in OpenAPI. Never return stack traces, database SQL, raw provider errors or credentials. Request IDs are generated/validated server-side and echoed in a response header.

## 9. Packages and subscriptions

### W1-060: Seed ten catalogue packages

Use the exact codes, prices, staff limits and numerical allowances in the blueprint. All are version 1, release status `planned`. Standard number limit 1; enterprise number limit 3. Enterprise starting prices are labelled `from`.

Feature permissions are explicit per package, not based on price comparisons or inheritance. Use a validated feature registry; unknown feature codes fail seeding. Examples: `core_inbox`, `contact_directory`, `business_settings`, `fixed_faq`, `notification_triggers`, `ai_answers`, `knowledge_base`, `catalogue`, `order_capture`, `calendar_booking`, `lead_qualification`, `ticketing`, `store_connector`, `campaign_segments`, `branch_routing`.

- Shared foundation features can be granted to all packages.
- Orders/appointments may grant their own FAQ/AI functions without inheriting every Receptionist document limit.
- Rule-only packages have AI allowance 0.
- Metrics not included are 0/absent according to one documented convention, never an accidental unlimited null.
- Catalogue feature permissions and implementation availability are separate. Week 1 only settings, contact directory, authentication and administration are implemented. No inbox/AI success display yet.
- `require_feature()` checks recognised feature code, actual capability implementation, membership/role, tenant state and subscription entitlement. Later usage enforcement is additional, not replaced by this helper.
- A paid `active` activation is unavailable in Week 1. Internal trial metadata does not trigger a charge or provider call.
- At this stage, show included allowances but display actual usage as `Not available yet`; do not fabricate counters at zero.

### W1-061: Subscription metadata

Record trial period instants and the assigned package-version reference consistently. Use a server clock and half-open periods. No scheduled renewals, automatic deductions, grace-period enforcement or invoices this week.

Service tests must prove package versions are immutable and snapshot references remain stable. Updating the future default package version must not silently mutate an existing subscription's price/limits.

## 10. Frontend implementation

### W1-070: Required routes and screens

| Screen | Required behaviour |
|---|---|
| `/login` | Email/password, submit/loading/error states, keyboard support, safe generic error; no public signup |
| `/workspaces` | Own memberships only, display business/role/status; no access to other workspaces |
| `/admin/tenants` | Operator metadata list/search, create-workspace form and suspend/reactivate action with reason |
| `/app/:tenantId/overview` | Business name, role, trial/package status and clear development feature availability |
| `/app/:tenantId/settings` | Load real settings, approved edit controls, field errors, save state and stale-version conflict |
| `/app/:tenantId/contacts` | Real paginated search/list, create/edit forms, active/archive filter and permitted archive/restore |
| `/app/:tenantId/team` | Read-only member summary for permitted roles; explain CLI provisioning during development |
| `/app/:tenantId/plan` | Included limits, package version, trial status; no invented usage or payment buttons |
| Forbidden/not-found/account-suspended | Clear state, safe navigation and logout |

### W1-071: UI and client rules

- One reusable app shell with business name, active workspace, role, sidebar and logout. Sidebar permissions reflect the backend matrix.
- Tenant brand name comes from data, not a build-time code replacement. Logo upload is deferred; a neutral initials/avatar placeholder is acceptable and labelled normally.
- Workspace change clears tenant-owned query caches, in-flight requests, forms and selected records. Query cache keys always include tenant ID.
- Protect against late A responses populating B after switching; cancel or discard outdated responses.
- Server remains the authority even if a user changes the URL or browser state.
- Show loading, empty, validation, permission, server-error and retry states on data screens.
- Use accessible labels/focus and confirmation for archive/suspend. Text content rendered safely, not arbitrary HTML.
- Frontend fetches via `/api`; includes cookies and CSRF for unsafe methods; normalises common errors and handles expired sessions.
- Display local business time zone for configuration; do not reinterpret stored UTC instants using the developer's PC time zone.
- LKR formatting based on minor units. No hardcoded company/customer names except synthetic fixtures.
- Future modules may appear as clearly unavailable cards; avoid fake interactive inboxes, order counters or analytics.
- UI initially English. Store language configuration and verify Sinhala/Tamil text round trips in forms; translated dashboard UI is a later scope decision.

## 11. Audit and operational visibility

### W1-080: Required events

Record tenant creation/suspension/reactivation, owner/membership provisioning/deactivation, settings changes, contact create/update/archive/restore, session creation/revocation and denied role/access events where useful.

- Successful tenant business mutation and its tenant audit commit together.
- Failed validation/denied access must not leave partial writes or misleading success audits.
- Login/access events can use separate structured operational logs; do not require a tenant audit before tenant identity is validated.
- Audit metadata records action/field names and safe identifiers; never passwords, cookies, CSRF values, full notes or raw contact exports.
- Structured logs: request ID, route template, method, status, duration and safe actor/tenant IDs when authenticated. Avoid query-string payloads and full request-body logging.
- No secret-bearing health/OpenAPI descriptions. No verbose SQL with bound credential values.
- Unexpected exceptions produce a safe 500 plus a redacted diagnostic tied to request ID.

## 12. CLI and synthetic data

### W1-090: Required commands

Provide documented commands equivalent to:

- Apply migrations through separate migration credentials.
- Provision a platform operator with hidden password prompt.
- Create a staff identity with hidden password prompt.
- Assign/deactivate a tenant membership through the shared authorisation/limit service.
- Seed demo tenants/packages/users/contacts in a development/test environment.
- Run tests/checks and display a safe schema/role diagnostic.

No credentials in CLI arguments, shell history or generated output. Passwords may be provided through a hidden interactive prompt or test-only ephemeral fixture mechanism. Reject demo seeding in production.

### W1-091: Demo fixture design

Create synthetic Restaurant A and Spare Parts B, using `order_desk` and `receptionist` trial metadata respectively. Suggested staff: one owner for each, a platform operator with no implicit membership, and a shared test identity who is manager in A and agent in B. This stays within 3 and 2 active staff limits.

- Separate settings, contacts and audit histories. Use the same synthetic contact phone value in both tenants to test permitted separation; never send messages or claim the number is unallocated.
- Include Sinhala/Tamil characters in some synthetic names/notes for Unicode persistence tests.
- Demo passwords are supplied at execution, not committed defaults.
- Seeding is idempotent for unchanged fixtures. A seed command must not overwrite user-edited data or reset passwords silently; destructive reset is explicit and restricted to a test target.
- Tenant/package lookup uses stable codes/slugs rather than assumptions about generated UUIDs.

## 13. Required verification matrix

Tests below are outcome requirements. The agent can combine related cases, but must show where each outcome is verified. Do not substitute only mocked HTTP tests for database isolation.

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Fresh database migration plus package/demo seed | Reproducible schema, grants and fixtures; rerun is safe |
| T02 | Runtime role ownership/privileges | No superuser, owner membership, `BYPASSRLS`, RLS-disable or truncate privilege |
| T03 | Password stored and login response | Argon2id hash only; no credential disclosure |
| T04 | Valid login and refresh | HttpOnly cookie, safe user/CSRF restore; no localStorage token |
| T05 | Unknown email vs wrong password | Same safe failure shape; dummy verification path |
| T06 | Logout/disabled identity/expired session | Old cookie cannot access protected routes |
| T07 | Idle and absolute deadlines | Correct boundaries using injected clock, no long sleeps |
| T08 | Missing/wrong CSRF or Origin on mutation | Denied without writes; allowed same-origin request succeeds |
| T09 | Login failure thresholds and Redis failure | 429 at documented limits; 503 when throttle unavailable |
| T10 | Unauthenticated/admin access | 401 without session; non-operator denied admin routes |
| T11 | Operator without tenant membership | No customer contact/settings-content access |
| T12 | User requests tenant without membership | Generic 403; no data/counts leaked |
| T13 | A reads/edits B contact ID under A route | 404; B unchanged |
| T14 | A supplies B `tenant_id` in body | Rejected; server never accepts tenant ownership from body |
| T15 | Runtime SQL without context | No scoped rows; scoped inserts fail |
| T16 | Runtime SQL with A context, no WHERE | Only A rows visible; B writes/moving tenant ID rejected |
| T17 | Pooled connection reuse and rollback | No A/B context leakage after commit/rollback |
| T18 | Parallel requests for A/B | Correct independent rows and audits |
| T19 | Manager in A / agent in B | Settings edit allowed only in A; roles not carried across tenant switch |
| T20 | Membership deactivation/tenant suspension | Existing session loses tenant operation access immediately |
| T21 | Concurrent staff provisioning at limit | Only permitted seats succeed; no over-allocation |
| T22 | Immutable package version / entitlement check | Existing plan unchanged; unimplemented capability not reported available |
| T23 | Tenant provisioning fails mid-transaction | No orphan tenant/subscription/membership/settings |
| T24 | Contact create/update/archive/restore | State/version/role rules enforced; safe repeat behaviour |
| T25 | Same contact phone in A/B; duplicate in A | Cross-tenant allowed; own-tenant duplicate safely rejected |
| T26 | Stale update version | 409; no overwrite or false success audit |
| T27 | Invalid hours/time zone/email/phone/extra fields | Safe 422; no writes |
| T28 | Search/pagination/Unicode | Bounded, stable, tenant-scoped; multilingual text survives |
| T29 | Suspended-account screen | Own metadata visible, tenant data blocked, logout works |
| T30 | Browser workspace switch including late response | No old business content or form appears in new workspace |
| T31 | Health dependency failure | Readiness 503; liveness accurately reports process state |
| T32 | Logs/error payloads/fixtures | No passwords, session tokens, raw notes or misleading provider claims |
| T33 | Required browser journey | Login → select A → edit settings → contact CRUD → switch B → confirm isolation → logout |

Frontend unit tests should focus on role visibility, form validation, conflict/error handling and cache clearing. Browser smoke tests cover the actual integration. Do not write tests merely asserting that a function called its mock.

## 14. Documentation and handoff

### W1-100: Required repository documents

- `README.md`: project purpose, Week 1 scope, prerequisites, startup/migrations/provisioning, local URLs, test commands, troubleshooting and limitations.
- `AGENTS.md`: read specs, preserve tenant checks, do not store secrets, run meaningful checks, no unsolicited future-week work, report failures honestly. This is repository guidance, not a custom ChatGPT skill.
- `docs/decisions/0001-platform-and-stack.md`: modular monolith, selected versions and non-cumulative package design.
- `docs/decisions/0002-tenant-isolation.md`: control-plane exceptions, runtime role, RLS and transaction-local context.
- `docs/decisions/0003-auth-sessions.md`: cookies, CSRF, expiry, throttling and provisioning boundaries.
- `docs/reports/week-01-completion.md`: requirements/tests matrix, commands/results, migration evidence, known gaps and founder walkthrough.
- OpenAPI-generated contract with safe examples.

### W1-101: Completion report must include

1. Commit identifier or source snapshot identifier and concise change summary.
2. Resolved runtime/dependency versions and migration head.
3. Exact verification commands and actual results, including failures/skips.
4. Evidence that isolation tests ran with the non-owner runtime role against PostgreSQL.
5. Screenshots of login, workspace selection, settings, contacts and package state using synthetic data only.
6. Demonstration of denied cross-tenant access and suspension behaviour.
7. Unimplemented features and external approvals plainly marked incomplete.
8. Any departures from these specifications and why they were proposed/accepted.
9. Paid expenditure incurred: expected zero for platform providers in Week 1.

No screenshot alone proves isolation. Include test evidence. Do not send `.env`, database dumps, cookies, real customer records or private credentials with the review bundle.

## 15. End-of-week acceptance checklist

- [ ] Proposal reviewed before implementation.
- [ ] Fresh local startup and migration replay documented and working.
- [ ] Ten package definitions correct; unimplemented modules visibly unavailable.
- [ ] Staff login/session/CSRF/expiry/throttling verified.
- [ ] Two tenant workspaces work with membership-specific roles.
- [ ] Settings and contact directory use real API/database data.
- [ ] Real PostgreSQL RLS tests pass using the runtime role.
- [ ] Concurrent seat limits, stale updates and atomic provisioning verified.
- [ ] Workspace switching cannot leak cached or late-response data.
- [ ] Mutations audited; errors/logs redact sensitive information.
- [ ] CI/build/browser checks pass, with no hidden required skips.
- [ ] Completion report and synthetic screenshots available.
- [ ] Founder can repeat the walkthrough and explain remaining gaps.

If a required item fails, Week 1 remains incomplete. Fix it before requesting Week 2. Do not reduce the acceptance criteria silently.

## 16. Prompt to give your coding agent first

```text
Read PROJECT_BLUEPRINT.md and WEEK_01_IMPLEMENTATION_SPEC.md completely.
Inspect my target repository and preserve any existing work.
Do not implement the application yet.

Create docs/plans/week-01-proposed-implementation.md covering every Week 1
requirement ID, selected supported dependency versions, exact file changes,
database schema/roles/migrations, tenant transaction context, staff sessions,
CSRF, API/UI contracts, test mapping and Windows/Docker commands.
Identify ambiguities and deviations instead of silently changing the spec.
Confirm there are no paid external API calls or future-week implementations.

Return the proposal and a concise list of decisions needing my review.
I will review it before asking you to implement.
```

After reviewing that proposal, the founder can authorise implementation in small slices. Bring the proposal here first if architectural review is wanted; after Week 1, bring the completion report and relevant source/tests for verification.

## 17. Source notes

This specification makes product-specific choices. Source guidance does not imply that copying sample code provides a complete secure platform.

- PostgreSQL policies and owner/bypass behaviour: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- SQLAlchemy transaction lifecycle: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
- OWASP session implementation: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP CSRF prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html

## 18. Change log

- 1.0: Detailed Week 1 foundation requirements, day slices, data/API/UI contracts, isolation tests and coding-agent review workflow. No actual application implementation has been performed.
