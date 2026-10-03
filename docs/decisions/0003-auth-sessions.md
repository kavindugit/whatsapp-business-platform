# ADR 0003: Authentication and Session Management

## Context
We need a secure authentication mechanism for users accessing the platform. The system handles sensitive business communications and settings, so security cannot be compromised. We need to defend against common web vulnerabilities like XSS, CSRF, and brute-force attacks.

## Decision
1. **Password Hashing**: We use Argon2id via `argon2-cffi`. Parameters: `time_cost=2`, `memory_cost=65536` (64 MB), `parallelism=2`, `hash_len=32`.
2. **Session Tokens**: We use stateful, opaque session tokens. The raw token is 32 cryptographic random bytes generated via `secrets.token_bytes(32)`. 
3. **Session Storage**: The token is stored in the database as a SHA-256 hash. The raw token is sent to the client as an `HttpOnly`, `SameSite=Lax` cookie.
4. **CSRF Protection**: A separate random CSRF token is stored in the database alongside the session. It is returned in the body of safe requests (like `/auth/me` or `/auth/login`) and must be presented as the `X-CSRF-Token` header on all unsafe requests (POST, PATCH, DELETE).
5. **Throttling**: We implement Redis-backed rate limiting for login attempts, keying off HMAC-pseudonymised IP addresses and email addresses.

## Rationale
- **Opaque Tokens over JWTs**: JWTs are difficult to revoke instantly. Stateful opaque tokens stored in the database allow immediate revocation (e.g., when a user is deactivated or logs out).
- **Hashed Tokens in DB**: If the database is compromised, active session tokens cannot be hijacked because only their SHA-256 hashes are stored.
- **Cookie Security**: `HttpOnly` prevents XSS attacks from stealing the session token. `SameSite=Lax` (and `Secure` in production) mitigates cross-site request forgery along with our explicit CSRF token requirement.
- **Argon2id**: Current OWASP recommendation over bcrypt.

## Consequences
- Every authenticated API request requires a database lookup to validate the session token. Given PostgreSQL's performance and connection pooling, this is an acceptable trade-off for immediate revokability and security.
- Clients (frontend) must manually attach the `X-CSRF-Token` header. This is handled centrally in our Axios interceptor.
