# Week 1 code review and correction checklist

Project: WhatsApp Business Automation Platform  
Repository: https://github.com/kavindugit/whatsapp-business-platform  
Reviewed commit: `7a324292f3f758bc10117a537e5ce84196a17f93`  
Review date: 2026-10-03  
Compared against: uploaded `week-01-proposed-implementation.md`, repository `docs/WEEK_01_IMPLEMENTATION_SPEC.md`, `docs/PROJECT_BLUEPRINT.md`, and `AGENTS.md`.

## Verdict

**Week 1 is substantially implemented, but it is not ready for acceptance. Complete the corrections below before starting Week 2.** Keep the shared multi-tenant architecture. These findings call for repairs and completion of the existing foundation, rather than separate projects for each package or customer.

No repository source was changed during this review. Dependencies were installed in the review environment and checks were run. No WhatsApp/OpenAI calls, production changes, messages, or paid services were used.

P1 means a functional/security/setup blocker to resolve before Week 2. P2 means a remaining Week 1 requirement that also needs completion for final acceptance. Evidence is identified as executed, source inspection, or still unverified.

## What is already present

- FastAPI backend, React dashboard, Docker development configuration, Alembic migration, and CI workflow.
- Argon2id password hashing, hashed session tokens, HttpOnly cookie helpers, CSRF comparison, Redis counters, and common error responses.
- Tenant memberships and owner/manager/agent permissions in backend dependencies.
- RLS enable/force statements and tenant `USING` / `WITH CHECK` policies for settings, contacts, and tenant audits.
- Ten package definitions in minor currency units, version references, planned release status, and trial metadata.
- Settings/contact endpoints and screens, platform tenant administration, workspace selector, and audit tables.

These are source-level observations. Their presence does not prove that the complete flows work or that real PostgreSQL isolation tests pass.

## Checks actually run

| Check | Result | Interpretation |
|---|---|---|
| Backend unit suite, with development-only test configuration | **17 passed** | Password/clock/session unit coverage passes; this is not integration acceptance. |
| `ruff check app/ tests/` | **352 findings** | Backend lint gate fails. |
| `ruff format --check app/ tests/` | **44 files need formatting** | Backend format gate fails. |
| `mypy app` | **84 errors in 17 files** | Backend type gate fails. |
| Frontend `npm run build` | **Fails TypeScript compilation** | Dashboard production build is not ready. |
| Frontend `npm run lint` | **Fails: ESLint flat configuration missing** | ESLint 9 cannot run the configured command. |
| Frontend `npm run test -- --run` | **4 tests passed, 2 suites failed** | Vitest mistakenly collects Playwright files. |
| `python -m app.cli --help` | **Fails: no module named app.cli** | Documented operator/staff/demo commands cannot run. |
| Isolated database-helper reproduction | **Raises InvalidRequestError** | Actual settings service tries to begin an already-started SQLAlchemy transaction. |
| Actual contact route with authentication/membership/DB service overridden only for Origin checking | **201 with missing Origin and 201 with an untrusted Origin** | Required Origin validation is absent on this route; this is not a live-database write test. |
| Pydantic request validation reproductions | **Version payloads rejected; forbidden extras and invalid settings accepted** | Confirms API contract and validation findings below. |
| Real PostgreSQL/Redis integration suite, migration replay, Docker startup, live browser journey | **Not run** | Docker and database/server executables were unavailable in the review environment. No isolation pass is claimed. |

Environment: Python 3.12.14, Node 24.19.0; frontend dependencies came from the committed npm lockfile. The project targets Node 22, so rerun the final gates on that version. Backend dependencies resolved from the declared ranges because no backend lockfile is committed. Counts above describe this review environment and may differ after dependencies are properly locked.

The initial backend unit attempt lacked required environment values. It was repeated with synthetic test configuration, producing the 17-pass result above; the initial configuration failures are not reported as product defects.

## Required corrections

### R01 — P1: Repair tenant transaction ownership and database result handling

**Locations:** `backend/app/db/tenant_context.py:75`; `backend/app/modules/tenancy/service.py:186–248`; `backend/app/modules/contacts/service.py:25–320`; `backend/app/modules/plans/service.py`.

**Problem:** Tenant services obtain a connection with `await db.connection()` from an `AsyncSession`, then call `conn.begin()` in `tenant_transaction`. The session has already started a transaction. This raises `InvalidRequestError` before the tenant SQL runs. Authentication/membership queries make transaction ownership especially important.

There is a second independent problem: `txn` is an `AsyncConnection`, but services execute `select(Contact)` / `select(BusinessSettings)` and use `.scalars()` as though an ORM session executed the query. A Core connection returns column values; `.scalar_one()` selects the first column rather than constructing an ORM object. Settings access to `.version` and contact DTO serialization therefore remain broken even after fixing the nested transaction.

**Implement:** Choose one consistent approach. The existing helper fits a fresh runtime connection with Core queries and explicit mapping/DTO construction. Alternatively, redesign the helper around a dedicated tenant ORM session and its transaction. Keep control-plane authentication separate from tenant SQL, and retain transaction-local `set_config(..., true)`, RLS, explicit tenant filters, and atomic audits. Do not fix this with privileged credentials or by disabling RLS. Avoid holding unused extra connections in `create_tenant`.

Return the updated DTO from the mutation transaction using `RETURNING` or a read inside the same transaction. Do not commit a successful write and then perform a fragile second read that can turn the response into a 500.

Also eagerly load `Package.versions` or construct a narrower package DTO in `get_tenant_subscription`. `PackageDTO.model_validate(package)` accesses a lazy relationship under async execution; without explicit loading it can fail with `MissingGreenlet`.

**Acceptance:** Real PostgreSQL endpoint tests successfully read/edit settings and perform contact CRUD using `app_runtime`. Repeated requests, rollback, pooled reuse, and concurrent A/B requests retain correct context and audit atomicity. Subscription serialization succeeds without lazy I/O.

**Evidence:** Actual settings-service reproduction raises the transaction error. A separate SQLAlchemy result-mechanics reproduction confirms a Core scalar returns a column, not a model. SQLite was used only for these library-mechanics demonstrations, never as an RLS/isolation substitute. The async package relationship finding is source inspection.

### R02 — P1: Make frontend mutation payloads match the backend

**Locations:** `frontend/src/api/contacts.ts:22,42,45`; `frontend/src/pages/dashboard/ContactsPage.tsx:118,151`; `frontend/src/pages/dashboard/SettingsPage.tsx:89`; backend contact/settings request schemas.

**Problem:** Settings save, contact edit, archive, and restore send `version`; their backend request models require `expected_version`. Valid UI actions return 422. Tenant status currently has a separate compatibility shim, making the contract inconsistent.

**Implement:** Use required positive `expected_version` consistently in all mutation schemas, API clients, forms, and tests. Remove permissive alternate fields once callers are updated. Give tenant creation an accurately typed response: backend returns `{tenant_id}`, while the client currently declares `TenantDetail`.

**Acceptance:** Use the actual browser forms to edit settings and create/edit/archive/restore contacts. Requests use the agreed contract, valid requests succeed, and stale versions produce `409 VERSION_CONFLICT`.

**Evidence:** Executed Pydantic checks reject the current frontend payload shapes because `expected_version` is missing.

### R03 — P1: Restore build, lint, type, and test gates

**Locations:** frontend `App.tsx`, `ErrorBoundary.tsx`, `components/ui/Card.tsx`, `src/tests/workspace.test.tsx`, `vite.config.ts`; backend lint/type output.

**Implement:**

- Add Vite client type declarations so `import.meta.env` is typed.
- Add required `override` modifiers to class members in `ErrorBoundary`.
- Type and forward supported native div props, including `style`, in `Card`.
- Handle the possibly undefined `initialGen` in the unit test.
- Add an ESLint 9 flat configuration with the actual React/TypeScript rules used by the project.
- Limit Vitest discovery to unit/component tests and exclude Playwright files.
- Fix backend lint/format/type errors. Use typed request fields, appropriate Optional annotations, typed async dependencies/results, and compatible Redis typings. Do not silence whole checks or disable strict mode to make CI green.

**Acceptance:** Build, lint, type, format, and unit commands pass from a fresh checkout with the agreed locked toolchain.

**Evidence:** Executed checks fail as shown in the results table.

### R04 — P1: Make dependency installation, test databases, and CI reproducible

**Locations:** `.github/workflows/ci.yml:49–51,105`; `backend/tests/conftest.py`; integration fixtures; `compose.yaml`; README; missing `uv.lock`, `pnpm-lock.yaml`, and Playwright configuration.

**Problems:**

- CI installs with `pnpm --frozen-lockfile`, but only `package-lock.json` is committed. Backend installs are also unlocked, despite the proposal promising `uv.lock`.
- CI sets `DATABASE_URL` and `TEST_DATABASE_URL` to the same value; conftest explicitly rejects that configuration.
- The migration step selects `psycopg2`, while project dependencies install psycopg 3.
- Local test fixture writes use `MIGRATION_DATABASE_URL`, normally targeting the development database, while the app is switched to the test database. A test can therefore seed/clean development data and query a different database.
- CI creates a migration owner without BYPASSRLS, while local bootstrap grants it BYPASSRLS. RLS fixture code assumes owner bypass despite FORCE RLS. Those fixtures are inconsistent across environments.
- Browser CI has an unfinished seed step and does not explicitly set up Node/pnpm. There is no committed Playwright configuration establishing the app URL and test discovery.

**Implement:** Select one frontend package manager and use its committed lockfile consistently; retain pnpm if following the agreed proposal, or document an npm deviation across Docker/CI/README. Lock backend dependencies. Use psycopg 3 everywhere.

Create explicitly separate development and test runtime/migration connection settings. Validate parsed database targets and environment before fixture writes or resets; do not use string equality alone as the safety check. Permit a correctly declared disposable test setup without requiring confusing fake URLs. Ensure fixture setup, migrations, and app requests all address the same disposable test database. Keep real runtime-role tests unprivileged, and use explicit fixture tenant context or a separate tightly scoped setup path. Do not give runtime BYPASSRLS to solve fixture failures.

Wire actual migrations and synthetic demo seeding into browser CI, configure the runner and baseURL, and run the required journey for changes before acceptance. Correct README port and setup statements to match Compose. The current Compose publishes loopback DB/Redis ports although README says they are not published.

**Acceptance:** Disposable fresh DB migration/seed/replay works; tests refuse unsafe targets; CI executes all gates and the meaningful browser journey. No fixture cleanup touches the development database.

### R05 — P1: Apply tenant suspension to every tenant-data operation

**Locations:** `backend/app/modules/tenancy/dependencies.py:55–70`; contact routes; settings GET; auth membership summary; frontend workspace selection.

**Problem:** `require_membership` checks membership but not tenant suspension. Settings reads and contact reads/create/update use that dependency. Archive/restore and settings edits use a separate role check that does enforce suspension. Suspension therefore protects only some operations.

**Implement:** Centralize active-tenant checking for all tenant-data routes, then add role checks where required. Keep login, `/auth/me`, workspace metadata selection, and logout available. Return tenant status separately from membership status; current summaries return active membership status even when the tenant is suspended. Route affected users to the suspended screen and block data queries/forms there.

**Acceptance:** Using an already-issued session, suspend A and verify every A contact/settings operation is denied immediately, B continues working, metadata/logout still work, and the workspace is labelled suspended.

**Evidence:** Dependency/route source inspection. This is not a claim that writes bypassed RLS in a live database.

### R06 — P1: Enforce Origin and login content-type requirements consistently

**Locations:** `backend/app/modules/auth/dependencies.py:22–27,80–88`; tenant/admin/contact routers; auth login route.

**Problem:** Only login/logout attach `require_origin`. `require_csrf` checks the token without validating Origin, so authenticated tenant/admin mutations omit the required second check. Login also lacks explicit JSON content-type enforcement.

**Implement:** Apply one unsafe-request dependency/middleware to every browser mutation: allowed Origin plus constant-time CSRF validation for authenticated actions. Login needs allowed Origin plus the agreed JSON media type before authentication work. Cover all unsafe methods supported by the API. CORS response configuration does not replace request rejection.

**Acceptance:** Missing/untrusted Origin is rejected even with a valid session and CSRF token, without calling the mutation service or writing an audit. Missing/wrong CSRF is rejected with an allowed Origin. Login rejects missing/unsupported content types according to the documented contract.

**Evidence:** Actual contact-route reproduction returned 201 for missing and untrusted Origin while authentication/membership and mutation persistence were isolated with test overrides. This establishes the missing guard, not an unauthenticated exploit.

### R07 — P1: Implement the documented operator/staff/demo CLI and seat-limit service

**Locations:** missing `backend/app/cli.py`; README CLI commands; `backend/tests/integration/test_concurrency.py:79–82`.

**Problem:** A fresh installation cannot provision its initial platform operator through the documented command. Staff creation, membership assignment/deactivation, demo seeding, and diagnostics are also advertised but absent. There is no completed shared service that proves active staff limits are enforced under concurrent provisioning.

**Implement:** Provide the documented equivalent commands: `provision-operator`, `create-user`, `assign-membership`, `deactivate-membership`, `seed-demo`, and `diagnose`. Use hidden password input, canonical emails, explicit operator authorization, safe metadata audits, and environment checks. Do not commit demo passwords or place real passwords in arguments/output.

Assign memberships through one transaction/service that locks a stable tenant row, reads the assigned package limit, counts active memberships, and handles activation/repeated assignment consistently. Count the active owner, exclude inactive memberships, enforce the one-active-owner constraint, and prohibit owner removal without the deferred replacement procedure. A workspace without an owner must be clearly pending provisioning.

Seed Restaurant A / Spare Parts B plus the shared manager-in-A/agent-in-B identity and Sinhala/Tamil data. Reruns must preserve edited data and passwords; reject production seeding.

**Acceptance:** All commands work from a fresh checkout. At the last seat, simultaneous assignments allow only the permitted result and record no false success audit. Deactivation takes effect on the next request. Demo seeding is repeatable and safe.

### R08 — P1: Make version checks atomic and conflict handling safe

**Locations:** contact update/archive/restore; `backend/app/modules/tenancy/service.py:166–180,207–227`.

**Problem:** Code reads the version, checks it in Python, then performs an UPDATE without checking the version in the database write. Two requests can both read version 1 and both report success. Status edits have the same race. The code raises generic `ConflictError` despite having a `VersionConflictError` class.

**Implement:** Use a version predicate and `RETURNING`, or a row lock with a version check under that lock. For example, update within the authorized tenant transaction where tenant ID, record ID, and `version = expected_version` all match; increment in the successful write. Correctly distinguish absent/foreign objects from stale versions without data leakage. Use `VERSION_CONFLICT` for stale writes.

Keep writes and success audits atomic. Handle unique phone/slug violations through rollback/savepoints or explicit transaction boundaries; do not continue using an aborted transaction. Define repeat archive/restore behaviour consistently with version semantics.

**Acceptance:** Two parallel edits using the same version yield one success and one 409, one version increment, and one success audit. Duplicate create/restore returns safe 409. Forced provisioning failure leaves no partial tenant/owner/subscription/settings/audit rows.

**Evidence:** Source inspection; concurrency outcomes must still be verified on PostgreSQL after R01 is corrected.

### R09 — P1: Complete request validation and prevent accidental settings/data loss

**Locations:** tenancy/contact/auth schemas, contact PATCH service, SettingsPage.

**Problems:** Request models silently ignore unknown fields. Injected `tenant_id` / `status` are accepted and dropped rather than rejected. Settings accept invalid IANA zones, arbitrary opening-hours shapes, and invalid phones. Slugs such as `a`, `admin`, and `a--b` are accepted. Settings UI lacks the planned opening-hours editor; the backend defaults omitted opening hours to `{}` and writes that default. Contact PATCH uses `is not None`, so optional fields cannot be cleared deliberately.

**Implement:**

- Use a common request base with `extra='forbid'`; keep response-model settings separate.
- Implement the specified 3–63 character slug rules, canonicalization, single hyphens, and reserved names.
- Validate plan codes, lengths, positive versions, trimmed non-empty names, password constraints for owner creation, and canonical staff email uniqueness.
- Validate time zones with `zoneinfo`; restrict currency to the initial supported value; normalize/validate phones consistently across frontend/backend.
- Model seven-day opening hours explicitly, including time format, overlap and overnight rules. Add the agreed editor and guidance.
- Decide/document PATCH semantics: omitted fields preserve values; explicit null clears nullable values. Use `model_fields_set` / `exclude_unset`, and prevent omitted settings from wiping saved hours or other optional data.
- Bound contact search and validate status filters. Keep parameterized queries and stable tenant-scoped pagination.

**Acceptance:** Invalid inputs/forbidden extras return safe 422 before writes; tests cover clearing nullable fields, preserving omitted values, saved hours, and Sinhala/Tamil round trips.

**Evidence:** Executed models accepted forbidden contact extras, invalid zone/phone/hours, and invalid/reserved slugs. Settings overwrite and null-clearing issues are source inspection.

### R10 — P1: Remove migration credentials from the API and protect logs

**Locations:** `backend/app/core/config.py:38`; `compose.yaml` API environment/env_file; `scripts/db-init.sh`; `backend/app/db/session.py:41`; exception logging.

**Problem:** Runtime Settings requires `MIGRATION_DATABASE_URL`, and Compose supplies that URL plus the full `.env` to the API. The local migration role has BYPASSRLS. This defeats the intended separation of runtime and privileged tooling. Development SQL echo also includes bound parameters; it can log password hashes, session hashes, CSRF values, and raw contact fields. Exception text can likewise include SQL parameters.

**Implement:** Separate migration/seed tooling configuration and environment from runtime API configuration. Use a one-off migration service/command with privileged credentials; the normal API environment must contain only runtime credentials. Avoid giving the API migration password variables indirectly through a broad env_file.

Disable sensitive SQL echo, enable appropriate parameter hiding, and ensure structured exception logging does not serialize SQL parameters or arbitrary customer data. Log safe event/request identifiers. Remove blanket pip trusted-host overrides from the Dockerfile; address certificate trust through an appropriate CA configuration rather than weakening package download verification.

**Acceptance:** The API starts with migration credentials absent. Runtime PostgreSQL role inspection confirms no ownership/superuser/BYPASSRLS/owner membership. Test logs after auth/contact successes and failures contain no sensitive values. All migrations still work through tooling.

### R11 — P2: Align session lifetime and failed-login throttling with the spec

**Locations:** auth dependency Cookie parameter; `backend/app/modules/auth/router.py:54`; throttle module; frontend/API proxy.

**Problems:** Login writes the configured cookie name, while authentication reads a hardcoded `session` cookie. The cookie expires 30 minutes after login and is never refreshed, even while server-side last_seen advances. Counters increment before authentication; success clears only the email counter, so successful logins still exhaust the IP budget. Through the current frontend proxy, client identity also needs explicit handling to avoid treating all staff as one source address.

**Implement:** Read the configured cookie consistently. Keep the server's 30-minute idle and 12-hour absolute limits authoritative; set the browser cookie deadline consistently or refresh it without exceeding absolute expiry. Reject at the deadline using the chosen half-open time semantics. Add `Cache-Control: no-store` for sensitive auth responses.

Implement/document the agreed failed-attempt budgets and boundary/reset rules. A separate general request limiter may be useful, but it must not silently replace failure counters. Account for concurrent attempts. Derive source IP through a controlled proxy configuration; never trust arbitrary forwarded headers. Keep Redis unavailable behaviour fail-closed with 503.

**Acceptance:** Custom cookie name works; active sessions survive beyond 30 minutes since login but idle/absolute expiry still denies access. Successful logins do not use the failed-login allowance. Email/IP thresholds, reset, concurrency, proxy identity, and Redis failure are tested.

### R12 — P1: Complete workspace-switch, permission, and error UI behaviour

**Locations:** WorkspaceContext; SettingsPage; ContactsPage; DashboardLayout; AuthContext; Overview; error pages.

**Problems:** WorkspaceContext creates an AbortController but does not expose/connect its signal to requests. Cache invalidation does not remove tenant data, and Overview uses a different cache-key prefix. Settings reset depends on numeric version rather than tenant identity and leaves the previous form when new settings are absent. Contact switching leaves archive confirmation/error state. Sidebar exposes manager-only pages to agents, SettingsPage has `canEdit = true`, and contact archive/restore buttons lack role gating. Several data errors look like empty/default content. Logout swallows a server failure and presents a signed-out UI even if the server session is still active.

**Implement:** Centralize query keys; consume TanStack Query cancellation signals in Axios; cancel/remove old tenant queries and clear tenant state on switching/logout. Handle direct route changes as well as the dropdown. Reset all forms, selected records, search, filters, confirmations, errors, and success flags by tenant identity. Guard late mutation callbacks with the tenant/action captured when the request began. Do not let late A results alter B's form or cache.

Derive UI permissions from the membership for the route tenant, matching the backend matrix. Make agent settings read-only; hide manager-only pages/actions. Handle 403/suspension/500/loading/retry explicitly. Complete required admin details/suspend confirmation and data-driven workspace overview; remove the hardcoded active-user count and inactive click-like actions. Treat logout failure explicitly and clear user-scoped cached data after a confirmed logout/expired session.

**Acceptance:** Delay A reads and saves, switch to B, and verify no A content, confirmation, success message, role, or form appears under B. Test manager-in-A/agent-in-B, direct URL changes, user change after logout, suspended access, server errors, and equal record version numbers across workspaces.

**Evidence:** Source inspection. Tenant-scoped query keys already provide useful separation; this finding does not assert a demonstrated cross-user server data leak. Existing workspace tests only exercise context state, not actual delayed network responses/forms.

### R13 — P2: Separate package inclusion from implemented capability availability

**Locations:** plans service/schemas; PlanPage feature rendering; missing shared `require_feature()` / capability registry.

**Problem:** A true package permission renders a green check even for unavailable inbox/AI/orders features. Week labels display mainly when a feature is not granted. No completed shared feature-availability enforcement helper was found.

**Implement:** Define recognized feature codes and actual implementation availability separately from package permission. Implement the specified helper checking identity/membership/role, tenant state, subscription entitlement, and actual capability readiness. Render distinct included-and-implemented, included-but-planned, and not-included states. Keep all ten packages planned and usage unavailable. Label enterprise starting prices appropriately. Do not build future modules or paid activation as part of this correction.

**Acceptance:** A package containing `ai_answers` still cannot use it in Week 1; UI says it is planned. Unknown codes fail safely. Existing package-version assignments remain immutable and the ten prices/limits match the blueprint.

### R14 — P2: Fix audit payloads and complete required safe events

**Locations:** `backend/app/modules/audit/service.py:21,42`; audit models `event_data`; direct table inserts in tenant/contact services; auth service/router.

**Problem:** ORM audit constructors set `metadata=...`, but the mapped Python attribute is `event_data`. The supplied dict becomes an unmapped instance attribute, leaving mapped event data unset. Direct JSONB inserts pass `json.dumps(...)`, resulting in a JSON string instead of the intended object. Mutation audit inserts omit request IDs; required login/logout/membership events are incomplete.

**Implement:** Use `event_data` for ORM construction and Python dictionaries for the Core JSONB column. Propagate server request IDs and safe changed-field metadata through services. Record the required auth/operator/membership/contact/settings events at the correct success/failure boundaries. Never record passwords, tokens, raw notes, or contact payloads. Preserve append-only grants and tenant RLS.

**Acceptance:** Read persisted audit records on PostgreSQL and assert JSON object shape, actor, tenant, request ID, action, and safe field metadata. Rejected/rolled-back mutations leave no success audit.

**Evidence:** Executed ORM construction shows `.metadata` contains the supplied dict while mapped `.event_data` is unset. JSONB double-encoding and missing events/IDs are source inspection.

### R15 — P1: Replace placeholder tests and provide the Week 1 evidence report

**Locations:** `backend/tests/integration/test_concurrency.py:79–82`; `frontend/tests/workspace.spec.ts:8`; `frontend/tests/e2e/journey.spec.ts:6`; `src/tests/workspace.test.tsx`; missing `docs/reports/week-01-completion.md`.

**Problem:** T21 contains only `pass`. The two Playwright tests assert `expect(true).toBeTruthy()` and never exercise the app. Workspace unit tests increment a generation counter without delaying an API response. Several original acceptance outcomes lack meaningful endpoint coverage, and test IDs do not consistently match the original specification. `test_day4.py:72` also expects `len(response.json()) == 10`, while `/packages` returns `{items: [...]}`.

**Implement:** Replace placeholders with tests of production services/routes and a genuine browser journey. Correct the catalogue response assertion. Map each original T01–T33 requirement to specific tests and evidence; mark anything not run as unverified. Add the agreed completion report with commands/results, clean-database setup, architectural deviations, and known limitations. Update the proposal's status and README claims to reflect actual implementation.

Minimum missing/completion coverage includes runtime role privileges; fresh migration/seed replay; operator without membership; foreign tenant/object requests; forbidden body tenant ID; pooled reuse after both commit and rollback; actual parallel A/B reads/writes/audits; role differences across tenants; suspension/deactivation; staff seat race; entitlement availability; provisioning rollback; contact lifecycle/duplicates/stale concurrent edits; validation/Unicode/pagination; dependency failures; secret-safe logs; and the full browser journey.

**Acceptance:** No unconditional pass assertions stand in for required outcomes. CI runs real PostgreSQL tests as the runtime role and a browser journey that edits settings, creates/edits/archives/restores a contact, switches to B, verifies separation, and logs out.

## Suggested order for the coding agent

1. **Database repair:** R01 + atomic write/audit foundation from R08/R14. Add real endpoint regression tests immediately.
2. **API and security:** R02, R05, R06, R09, R10, R11. Verify all role/suspension/Origin rules and payload semantics.
3. **Setup and staff management:** R07 and database safety from R04. Make a fresh installation usable.
4. **Frontend completion:** R03 frontend fixes, R12, R13; verify actual forms and failure states.
5. **Acceptance:** Complete backend checks, lockfiles/CI, R15, fresh database replay, and the completion report.

Use small reviewable commits. Implement Week 1 repairs only. Do not add WhatsApp webhooks, OpenAI, payments, order/booking engines, or production deployment in this correction pass.

## Ready-to-send coding-agent instruction

> Review `AGENTS.md`, `docs/WEEK_01_IMPLEMENTATION_SPEC.md`, the blueprint, and this review. Prepare a correction implementation plan addressing R01–R15 in the recommended order. Identify exact files, transaction ownership, API contracts, database safety, migration effects, and regression tests. Preserve the shared multi-tenant design and all runtime RLS/privilege boundaries. Do not treat placeholders as acceptance evidence or add Week 2 features. After implementation, run the documented gates on the agreed locked toolchain, migrate/seed/replay a disposable real PostgreSQL database, run actual runtime-role isolation and concurrency tests plus the full browser journey, and produce `docs/reports/week-01-completion.md` mapping T01–T33 to evidence. Report failures and unexecuted checks explicitly. Do not spend money, call providers, or deploy production.

## Week 1 acceptance gate

- [ ] Fresh checkout installs from committed lockfiles and builds.
- [ ] Separate tooling credentials; runtime starts without privileged credentials.
- [ ] Fresh migration, demo seed, repeat seed, and clean replay verified on disposable databases.
- [ ] Operator/staff/membership/diagnostic commands work safely.
- [ ] Tenant settings/contact endpoints return correct DTOs and preserve RLS context.
- [ ] Roles, suspension/deactivation, Origin/CSRF, sessions, throttling, and validations are tested.
- [ ] Atomic version/seat-limit races, duplicate handling, provisioning rollback, and audits verified.
- [ ] UI forms, cancellation, workspace changes, permission states, and retry/errors verified.
- [ ] Capabilities distinguish planned inclusion from implemented availability.
- [ ] All backend/frontend quality gates and meaningful integration/browser tests pass.
- [ ] T01–T33 completion evidence is written; no unverified item is labelled passed.

## Technical references

The code findings use the reviewed commit, not assumptions about newer repository changes.

- SQLAlchemy transaction/autobegin behaviour: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#auto-begin
- SQLAlchemy Core versus ORM SELECT results: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
- Original acceptance requirements: repository `docs/WEEK_01_IMPLEMENTATION_SPEC.md`, especially W1-013, W1-030/031, W1-040–043, W1-051, W1-060, W1-071, W1-080–091, and T01–T33.

For source links, open https://github.com/kavindugit/whatsapp-business-platform/tree/7a324292f3f758bc10117a537e5ce84196a17f93 and use the paths/lines above. Line numbers identify this reviewed version and will change after fixes.
