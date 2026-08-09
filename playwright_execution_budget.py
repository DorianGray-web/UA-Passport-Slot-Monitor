"""Process-safe global pacing for bounded Playwright discovery sessions."""

from __future__ import annotations

import random
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


class PlaywrightExecutionBudget:
    """Persist and enforce one anonymous global browser start budget."""

    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        random_uniform: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self.path = path
        self._clock = clock
        self._monotonic = monotonic
        self._sleeper = sleeper
        self._random_uniform = random_uniform
        self._initialize()

    def wait_until_allowed(
        self,
        timeout_seconds: float,
        *,
        poll_interval_seconds: float = 0.1,
    ) -> float | None:
        """Return seconds waited when the budget opens, or ``None`` on timeout."""
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        started = self._monotonic()
        deadline = started + timeout_seconds
        while True:
            if self._is_allowed(self._clock()):
                return max(0.0, self._monotonic() - started)
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                return None
            self._sleeper(min(poll_interval_seconds, remaining))

    def defer_next(
        self,
        *,
        min_interval_seconds: float,
        max_interval_seconds: float,
    ) -> datetime:
        """Persist the earliest time at which another browser may start."""
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        if max_interval_seconds < min_interval_seconds:
            raise ValueError(
                "max_interval_seconds must be greater than or equal to "
                "min_interval_seconds"
            )
        interval_seconds = self._random_uniform(
            min_interval_seconds,
            max_interval_seconds,
        )
        next_start_at = self._clock() + timedelta(seconds=interval_seconds)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE playwright_execution_budget
                SET next_start_at=?
                WHERE singleton=1
                """,
                (_timestamp(next_start_at),),
            )
            connection.commit()
        return next_start_at

    def _initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS playwright_execution_budget (
                    singleton INTEGER PRIMARY KEY CHECK (singleton=1),
                    next_start_at TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO playwright_execution_budget(
                    singleton, next_start_at
                ) VALUES (1, NULL)
                """
            )

    def _is_allowed(self, now: datetime) -> bool:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT next_start_at
                FROM playwright_execution_budget
                WHERE singleton=1
                """
            ).fetchone()
        return row is None or row[0] is None or row[0] <= _timestamp(now)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            yield connection
        finally:
            connection.close()
