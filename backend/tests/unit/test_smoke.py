"""
tests/unit/test_smoke.py
Day 1 smoke tests — verify core module imports and configuration validation.
Real database/auth tests are added in Day 2 and 3.
"""
from __future__ import annotations

import os

import pytest


class TestConfigImport:
    """Verify the config module loads without errors."""

    def test_settings_module_importable(self) -> None:
        from app.core.config import Settings  # noqa: F401
        assert Settings is not None

    def test_settings_validates_missing_required(self) -> None:
        """Settings should fail clearly when required values are absent."""
        from pydantic import ValidationError
        from app.core.config import Settings

        with pytest.raises((ValidationError, Exception)):
            Settings(
                database_url="",  # Empty — should fail
                migration_database_url="",
                session_secret_key="",
                throttle_pseudonym_secret="",
            )

    def test_secret_key_too_short_rejected(self) -> None:
        """Short session secret keys must be rejected."""
        from pydantic import ValidationError
        from app.core.config import Settings

        with pytest.raises((ValidationError, ValueError)):
            Settings(
                app_env="development",
                database_url="postgresql+psycopg://user:pass@db:5432/dev",
                migration_database_url="postgresql+psycopg://owner:pass@db:5432/dev",
                session_secret_key="tooshort",  # < 32 bytes
                throttle_pseudonym_secret="alsovalidenoughsecret1234567890",
            )

    def test_changeme_placeholder_rejected(self) -> None:
        """CHANGEME placeholder values must be rejected."""
        from pydantic import ValidationError
        from app.core.config import Settings

        with pytest.raises((ValidationError, ValueError)):
            Settings(
                app_env="development",
                database_url="postgresql+psycopg://user:pass@db:5432/dev",
                migration_database_url="postgresql+psycopg://owner:pass@db:5432/dev",
                session_secret_key="CHANGEME_at_least_32_random_bytes_here",
                throttle_pseudonym_secret="valid_throttle_secret_long_enough",
            )


class TestClockModule:
    """Verify the clock abstraction works correctly."""

    def test_system_clock_returns_utc(self) -> None:
        from datetime import timezone
        from app.core.clock import SystemClock

        clock = SystemClock()
        now = clock.utcnow()
        assert now.tzinfo == timezone.utc

    def test_fixed_clock_returns_fixed_time(self) -> None:
        from datetime import datetime, timezone
        from app.core.clock import FixedClock

        fixed_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        clock = FixedClock(fixed_time)
        assert clock.utcnow() == fixed_time

    def test_fixed_clock_advance(self) -> None:
        from datetime import datetime, timedelta, timezone
        from app.core.clock import FixedClock

        start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        clock = FixedClock(start)
        clock.advance(minutes=31)
        assert clock.utcnow() == start + timedelta(minutes=31)

    def test_fixed_clock_requires_timezone(self) -> None:
        from datetime import datetime
        from app.core.clock import FixedClock

        naive = datetime(2026, 1, 1, 12, 0, 0)  # No tzinfo
        with pytest.raises(ValueError):
            FixedClock(naive)


class TestSecurityModule:
    """Verify security utilities work correctly."""

    def test_password_hashes_and_verifies(self) -> None:
        from app.core.security import hash_password, verify_password

        password = "correct-horse-battery-staple"
        hashed = hash_password(password)

        assert hashed != password  # Not stored plaintext
        assert hashed.startswith("$argon2id")  # Argon2id variant
        assert verify_password(password, hashed) is True
        assert verify_password("wrong-password", hashed) is False

    def test_dummy_hash_does_not_raise(self) -> None:
        from app.core.security import dummy_password_check

        # Must not raise any exception
        dummy_password_check("any-attempted-password")

    def test_session_token_entropy(self) -> None:
        from app.core.security import generate_session_token

        token = generate_session_token()
        assert len(token) == 64  # 32 bytes = 64 hex chars
        assert token != generate_session_token()  # Randomness

    def test_session_token_hash_differs_from_raw(self) -> None:
        from app.core.security import generate_session_token, hash_session_token

        raw = generate_session_token()
        hashed = hash_session_token(raw)
        assert hashed != raw
        assert len(hashed) == 64  # SHA-256 hex

    def test_csrf_constant_time_compare(self) -> None:
        from app.core.security import generate_csrf_token, verify_csrf_token

        token = generate_csrf_token()
        assert verify_csrf_token(token, token) is True
        assert verify_csrf_token(token, "different-token") is False
        assert verify_csrf_token("", token) is False

    def test_different_passwords_produce_different_hashes(self) -> None:
        from app.core.security import hash_password

        h1 = hash_password("password1")
        h2 = hash_password("password1")  # Same password, different salts
        # Argon2id uses random salts — same password produces different hashes
        assert h1 != h2
