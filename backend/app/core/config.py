"""
app/core/config.py
Application configuration loaded from environment variables.
Validation fails loudly on startup if required values are missing or invalid.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration for the platform.
    Values are read from environment variables (case-insensitive).
    See .env.example for documentation on each variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars; don't fail on Docker extras
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = Field(default="development", pattern=r"^(development|test|production)$")
    app_label: str = Field(default="whatsapp-business-platform")
    api_prefix: str = Field(default="/api/v1")
    allowed_origins: str = Field(default="http://localhost:5173")

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(...)  # Required; runtime role
    migration_database_url: str = Field(...)  # Required; migration role only

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://redis:6379/0")

    # ── Session ───────────────────────────────────────────────────────────────
    session_cookie_name: str = Field(default="session")
    session_idle_minutes: Annotated[int, Field(ge=1, le=1440)] = Field(default=30)
    session_absolute_hours: Annotated[int, Field(ge=1, le=168)] = Field(default=12)
    session_secret_key: str = Field(...)  # Required; must be ≥32 bytes when decoded

    # ── Login throttling ──────────────────────────────────────────────────────
    throttle_max_email_attempts: Annotated[int, Field(ge=1, le=100)] = Field(default=5)
    throttle_max_ip_attempts: Annotated[int, Field(ge=1, le=500)] = Field(default=20)
    throttle_window_minutes: Annotated[int, Field(ge=1, le=60)] = Field(default=15)
    throttle_pseudonym_secret: str = Field(...)  # Required; separate from session secret

    # ── Test database ─────────────────────────────────────────────────────────
    test_database_url: str = Field(default="")

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def parsed_allowed_origins(self) -> list[str]:
        """Return allowed origins as a list, stripping whitespace."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("session_secret_key")
    @classmethod
    def validate_secret_key_length(cls, v: str) -> str:
        if len(v.encode()) < 32:
            raise ValueError("SESSION_SECRET_KEY must be at least 32 bytes")
        if v.startswith("CHANGEME"):
            raise ValueError("SESSION_SECRET_KEY must be changed from the placeholder")
        return v

    @field_validator("throttle_pseudonym_secret")
    @classmethod
    def validate_throttle_secret(cls, v: str) -> str:
        if len(v.encode()) < 16:
            raise ValueError("THROTTLE_PSEUDONYM_SECRET must be at least 16 bytes")
        if v.startswith("CHANGEME"):
            raise ValueError("THROTTLE_PSEUDONYM_SECRET must be changed from the placeholder")
        return v

    @model_validator(mode="after")
    def validate_production_requirements(self) -> Settings:
        if self.is_production:
            # Production must not use any development defaults
            if "localhost" in self.allowed_origins or "127.0.0.1" in self.allowed_origins:
                raise ValueError("ALLOWED_ORIGINS must not include localhost in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings.
    Cached after first call; use only after application startup.
    In tests, call get_settings.cache_clear() and set TEST_* env vars.
    """
    return Settings()
