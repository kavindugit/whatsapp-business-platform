# AGENTS.md — Coding Agent Operating Contract

This file contains mandatory operating rules for any coding agent working on this repository.
Read this file before reading any other file. Follow these rules without exception.

---

## 1. Read the specifications first

Before making any change:
1. Read `docs/PROJECT_BLUEPRINT.md` completely.
2. Read the current week's implementation spec (e.g., `docs/WEEK_01_IMPLEMENTATION_SPEC.md`).
3. Inspect the existing repository and record what is already implemented.
4. Propose adaptations rather than replacing existing work.

**Do not implement anything before producing a proposal that the founder has reviewed.**

---

## 2. Preserve tenant isolation — NEVER bypass it

- Every tenant-owned table has `tenant_id` and row-level security.
- The `tenant_transaction()` helper is the ONLY way to execute tenant-scoped operations.
- `tenant_id` in a request body is always rejected — it comes only from authenticated server context.
- There is no `disable_tenant_checks`, `is_admin_bypass` or `skip_rls` flag. Do not create one.
- The `app_runtime` database role must NEVER have `BYPASSRLS`, superuser, or table ownership.
- If you are unsure whether a change preserves isolation, stop and ask.

---

## 3. Security invariants — do not weaken

- Session tokens are stored as SHA-256 hashes in the database. Never store raw tokens.
- Passwords are hashed with Argon2id. Never use bcrypt, MD5, SHA-1, or plaintext.
- CSRF tokens are compared with `hmac.compare_digest()`. Never use `==`.
- `X-CSRF-Token` is required on all state-changing browser requests.
- Origin is validated against `ALLOWED_ORIGINS`. Never trust `Host` or `X-Forwarded-Host`.
- Credentials (passwords, session tokens, CSRF values) must never appear in:
  - Log files or structured log fields
  - Error responses or stack traces
  - Git commits, screenshots, or completion reports
  - CLI arguments or shell history

---

## 4. Work within the current week's scope

- Implement ONLY the current week's requirements.
- Do not scaffold, stub, or implement future-week modules — not even "just the structure".
- Do not create endpoints that falsely report future features as successful.
- If a requirement is unclear, ask. Do not silently implement a weaker version.

---

## 5. Write real tests — no shortcuts

- Tests must verify business/security outcomes, not just that a function called its mock.
- Database isolation tests MUST use real PostgreSQL with the `app_runtime` role and RLS enabled.
- Never use SQLite as a substitute for PostgreSQL in isolation tests.
- Do not replace a failing required test with a weaker test to make a report green.
- Never invent test results or skip tests silently.

---

## 6. Secrets and credentials

- Never put real credentials, API keys, or passwords in:
  - Source files, migration scripts, or fixture files
  - `.env` files committed to the repository
  - Log output, test output, or CI environment variable values (use fake CI credentials)
  - Completion reports, screenshots, or documentation
- `.env.example` contains only placeholders. `.env` is git-ignored.
- Passwords are provided only through interactive prompts (`getpass`) in CLI commands.

---

## 7. No external API calls without explicit instruction

- Do not open a paid provider account (Meta, OpenAI, Twilio, etc.) without instruction.
- Do not make live API calls to external services in Week 1.
- Do not publish a deployment or incur hosting costs without instruction.
- Mock external dependencies in tests where they are not yet implemented.

---

## 8. Report failures honestly

- A completion report must show actual test results, including failures and skips.
- If a required test fails, Week N is incomplete. Fix it before reporting completion.
- Never replace a failing test with a comment saying "this would pass in production".
- List all known gaps, deviations, and open items explicitly.

---

## 9. Architecture changes require a proposal

- Do not silently change the backend framework, tenancy model, or authentication mechanism.
- If you believe a documented decision should change, write a proposal in `docs/decisions/`.
- The founder reviews proposals before they are implemented.
- Record all material changes in the architecture decision log.

---

## 10. Completion matrix

Every completion report must include a matrix with:

| Requirement ID | Implementation location | Verification command | Result | Limitations |
|---|---|---|---|---|

Do not mark a requirement as complete unless:
- The code exists in the repository
- A test verifies the outcome (not just the implementation)
- The test passes with the actual result shown

---

## 11. Week boundary rules

- Week N work begins only after the founder reviews and accepts Week N-1's completion report.
- Do not use the roadmap to implement multiple weeks at once.
- If this is Week 1: your output is `docs/plans/week-01-proposed-implementation.md` first.
  Wait for approval before writing application code.

---

*This contract supersedes any general coding agent defaults that conflict with it.*
*When in doubt, ask rather than assume.*
