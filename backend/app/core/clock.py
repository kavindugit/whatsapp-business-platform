"""
app/core/clock.py
Injectable UTC clock abstraction for deterministic time-dependent tests.

Usage in production:
    from app.core.clock import SystemClock
    clock = SystemClock()
    now = clock.utcnow()

Usage in tests:
    from app.core.clock import FixedClock
    from datetime import datetime, timezone
    fixed = FixedClock(datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc))
    # advance time
    fixed.advance(minutes=31)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta


class AbstractClock(ABC):
    """Abstract clock interface. All time access goes through this."""

    @abstractmethod
    def utcnow(self) -> datetime:
        """Return the current UTC time as a timezone-aware datetime."""
        ...


class SystemClock(AbstractClock):
    """Production clock: delegates to the real system time."""

    def utcnow(self) -> datetime:
        return datetime.now(tz=UTC)


class FixedClock(AbstractClock):
    """
    Test clock: returns a fixed point in time that can be advanced manually.
    Never use in production code.
    """

    def __init__(self, fixed_time: datetime) -> None:
        if fixed_time.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware datetime")
        self._time = fixed_time

    def utcnow(self) -> datetime:
        return self._time

    def advance(
        self,
        *,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
    ) -> None:
        """Advance the clock by the given duration."""
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        self._time = self._time + delta

    def set(self, new_time: datetime) -> None:
        """Set the clock to an absolute time."""
        if new_time.tzinfo is None:
            raise ValueError("FixedClock.set requires a timezone-aware datetime")
        self._time = new_time


# Default system clock instance used in production
system_clock = SystemClock()
