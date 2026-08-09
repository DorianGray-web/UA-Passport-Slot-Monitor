"""Anonymous, process-safe FIFO lease for bounded Playwright operations."""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class PlaywrightLeaseToken:
    """Opaque proof that one bounded Playwright operation may proceed."""

    value: str


class SQLitePlaywrightLease:
    """Provide one anonymous FIFO lease backed by a local SQLite database."""

    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.path = path
        self._clock = clock
        self._monotonic = monotonic
        self._sleeper = sleeper
        self._initialize()

    def acquire(
        self,
        timeout_seconds: float,
        lease_seconds: float,
        *,
        poll_interval_seconds: float = 0.1,
    ) -> PlaywrightLeaseToken | None:
        """Wait in FIFO order for one absolute-TTL lease, or return ``None``."""
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        token = PlaywrightLeaseToken(uuid4().hex)
        self._enqueue(token, timeout_seconds)
        deadline = self._monotonic() + timeout_seconds
        while True:
            if self._claim_if_head(token, lease_seconds):
                return token
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                self._abandon(token)
                return None
            self._sleeper(min(poll_interval_seconds, remaining))

    def release(self, token: PlaywrightLeaseToken) -> bool:
        """Release an active lease. Expired or stale tokens cannot release it."""
        if not isinstance(token, PlaywrightLeaseToken):
            raise TypeError("token must be a PlaywrightLeaseToken")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE playwright_lease_tickets
                SET status='released', lease_until=NULL
                WHERE token=? AND status='active'
                """,
                (token.value,),
            )
            connection.commit()
            return cursor.rowcount == 1

    def _initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS playwright_lease_tickets (
                    ticket INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL CHECK (
                        status IN ('waiting', 'active', 'released', 'expired', 'abandoned')
                    ),
                    enqueued_at TEXT NOT NULL,
                    wait_until TEXT,
                    lease_until TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_playwright_lease_waiting
                ON playwright_lease_tickets(status, ticket)
                """
            )
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(playwright_lease_tickets)"
                )
            }
            if "wait_until" not in columns:
                connection.execute(
                    "ALTER TABLE playwright_lease_tickets ADD COLUMN wait_until TEXT"
                )
                connection.execute(
                    """
                    UPDATE playwright_lease_tickets
                    SET wait_until=enqueued_at
                    WHERE status='waiting' AND wait_until IS NULL
                    """
                )

    def _enqueue(
        self,
        token: PlaywrightLeaseToken,
        timeout_seconds: float,
    ) -> None:
        now = self._clock()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO playwright_lease_tickets(
                    token, status, enqueued_at, wait_until
                ) VALUES (?, 'waiting', ?, ?)
                """,
                (
                    token.value,
                    _timestamp(now),
                    _timestamp(now + timedelta(seconds=timeout_seconds)),
                ),
            )

    def _claim_if_head(
        self,
        token: PlaywrightLeaseToken,
        lease_seconds: float,
    ) -> bool:
        now = self._clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE playwright_lease_tickets
                SET status='expired', lease_until=NULL
                WHERE status='active' AND lease_until <= ?
                """,
                (_timestamp(now),),
            )
            connection.execute(
                """
                UPDATE playwright_lease_tickets
                SET status='expired'
                WHERE status='waiting' AND token != ? AND wait_until <= ?
                """,
                (token.value, _timestamp(now)),
            )
            head = connection.execute(
                """
                SELECT token, status
                FROM playwright_lease_tickets
                WHERE status IN ('waiting', 'active')
                ORDER BY ticket
                LIMIT 1
                """
            ).fetchone()
            if head is None or head[0] != token.value or head[1] != "waiting":
                connection.commit()
                return False
            cursor = connection.execute(
                """
                UPDATE playwright_lease_tickets
                SET status='active', lease_until=?
                WHERE token=? AND status='waiting'
                """,
                (_timestamp(now + timedelta(seconds=lease_seconds)), token.value),
            )
            connection.commit()
            return cursor.rowcount == 1

    def _abandon(self, token: PlaywrightLeaseToken) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE playwright_lease_tickets
                SET status='abandoned'
                WHERE token=? AND status='waiting'
                """,
                (token.value,),
            )
            connection.commit()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            yield connection
        finally:
            connection.close()
