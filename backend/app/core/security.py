"""
app/core/security.py
CSRF protection, Origin validation, session cookie helpers, and
password hashing utilities.

CSRF strategy (W1-041):
  - Login: requires Content-Type: application/json + allowed Origin
  - All other unsafe methods: requires X-CSRF-Token header + allowed Origin
  - CSRF token compared with constant-time hmac.compare_digest()
  - Token stored in auth_sessions, returned in login/me responses
  - Never stored in localStorage; lives only in server session + memory

Origin validation (W1-041):
  - Validated against ALLOWED_ORIGINS config list
  - Never trust Host, X-Forwarded-Host, or Referer for security decisions
  - No wildcard credentialed CORS
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING

import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Request

from app.core.errors import ForbiddenError, UnauthorizedError

if TYPE_CHECKING:
    pass

# ── Argon2id configuration ─────────────────────────────────────────────────────
# Minimum OWASP-aligned parameters. Adjust memory_cost upward on higher-RAM servers.
_hasher = PasswordHasher(
    time_cost=2,        # Number of iterations
    memory_cost=65536,  # 64 MB memory
    parallelism=2,      # Parallel threads
    hash_len=32,        # Output hash length in bytes
    salt_len=16,        # Random salt length in bytes
    encoding="utf-8",
    type=argon2.Type.ID,  # Argon2id variant
)

# Dummy hash used when the user email is not found — prevents timing attacks
# This value is pre-computed and never matches any real password.
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=2,p=2$"
    "AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)


def hash_password(password: str) -> str:
    """Hash a plain-text password with Argon2id. Returns the encoded hash string."""
    return _hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plain-text password against an Argon2id hash.
    Returns True if valid, False otherwise.
    Does NOT raise; safe to call even with an intentionally invalid dummy hash.
    """
    try:
        return _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def dummy_password_check(attempted_password: str) -> None:
    """
    Perform a dummy Argon2id verification to prevent timing-based user enumeration.
    Called when the login email is not found in the database.
    Always returns without error; the result is discarded.
    """
    verify_password(attempted_password, _DUMMY_HASH)


# ── Session token generation ───────────────────────────────────────────────────

def generate_session_token() -> str:
    """Generate a cryptographically random session token (256 bits = 32 bytes, hex-encoded)."""
    return secrets.token_hex(32)  # 64-character hex string


def hash_session_token(raw_token: str) -> str:
    """SHA-256 hash of the raw session token for storage. Never store the raw token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_csrf_token() -> str:
    """Generate a cryptographically random CSRF token."""
    return secrets.token_hex(32)


def verify_csrf_token(provided: str, expected: str) -> bool:
    """
    Constant-time comparison of CSRF tokens.
    Returns True if they match; False otherwise.
    """
    return hmac.compare_digest(provided.encode(), expected.encode())


# ── Origin validation ──────────────────────────────────────────────────────────

def validate_origin(request: Request, allowed_origins: list[str]) -> None:
    """
    Validate that the request Origin header is in the allowed list.
    Raises ForbiddenError if:
      - Origin header is absent
      - Origin is not in the allowed list
    Does not trust X-Forwarded-Host or Host headers for this check.
    """
    origin = request.headers.get("origin")
    if not origin:
        raise ForbiddenError(
            "Origin header is required for this request.",
        )
    if origin not in allowed_origins:
        raise ForbiddenError(
            "This origin is not permitted.",
        )


def validate_csrf(request: Request, session_csrf_token: str) -> None:
    """
    Validate the X-CSRF-Token header against the session's stored CSRF token.
    Raises UnauthorizedError if missing; ForbiddenError if invalid.
    """
    provided = request.headers.get("x-csrf-token")
    if not provided:
        raise UnauthorizedError("CSRF token is required.")
    if not verify_csrf_token(provided, session_csrf_token):
        raise ForbiddenError("CSRF token is invalid.")


# ── Cookie helpers ─────────────────────────────────────────────────────────────

def session_cookie_kwargs(
    *,
    cookie_name: str,
    value: str,
    max_age_seconds: int,
    is_production: bool,
) -> dict[str, object]:
    """
    Return keyword arguments for setting the session cookie.
    Secure flag is set only in production (HTTPS required).
    Development on localhost may omit Secure; this is not a general production toggle.
    """
    return {
        "key": cookie_name,
        "value": value,
        "httponly": True,
        "samesite": "lax",
        "path": "/",
        "secure": is_production,
        "max_age": max_age_seconds,
    }


def clear_session_cookie_kwargs(*, cookie_name: str, is_production: bool) -> dict[str, object]:
    """Return kwargs to clear (expire) the session cookie on the client."""
    return {
        "key": cookie_name,
        "value": "",
        "httponly": True,
        "samesite": "lax",
        "path": "/",
        "secure": is_production,
        "max_age": 0,
    }
