from __future__ import annotations

import sqlite3
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright_lease import SQLitePlaywrightLease


class ManualClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class SQLitePlaywrightLeaseTests(unittest.TestCase):
    def make_lease(
        self,
        root: Path,
        *,
        clock: ManualClock | None = None,
    ) -> SQLitePlaywrightLease:
        return SQLitePlaywrightLease(
            root / "playwright-lease.sqlite3",
            clock=clock or ManualClock(),
        )

    def test_releases_one_opaque_lease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lease = self.make_lease(root)
            token = lease.acquire(0, 30)

            self.assertIsNotNone(token)
            self.assertTrue(lease.release(token))
            self.assertFalse(lease.release(token))
            connection = sqlite3.connect(root / "playwright-lease.sqlite3")
            try:
                columns = [
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(playwright_lease_tickets)"
                    )
                ]
            finally:
                connection.close()
            self.assertEqual(
                columns,
                [
                    "ticket",
                    "token",
                    "status",
                    "enqueued_at",
                    "wait_until",
                    "lease_until",
                ],
            )

    def test_absolute_ttl_allows_recovery_after_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = ManualClock()
            lease = self.make_lease(Path(directory), clock=clock)
            stale = lease.acquire(0, 10)
            self.assertIsNotNone(stale)

            clock.advance(11)
            recovered = lease.acquire(0, 10)

            self.assertIsNotNone(recovered)
            self.assertNotEqual(stale, recovered)
            self.assertFalse(lease.release(stale))
            self.assertTrue(lease.release(recovered))

    def test_wait_timeout_abandons_ticket_without_blocking_following_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lease = self.make_lease(root)
            active = lease.acquire(0, 30)
            self.assertIsNotNone(active)

            timed_out = lease.acquire(0, 30)
            self.assertIsNone(timed_out)
            self.assertTrue(lease.release(active))

            following = lease.acquire(0, 30)
            self.assertIsNotNone(following)
            self.assertTrue(lease.release(following))

            connection = sqlite3.connect(root / "playwright-lease.sqlite3")
            try:
                statuses = [
                    row[0]
                    for row in connection.execute(
                        "SELECT status FROM playwright_lease_tickets ORDER BY ticket"
                    )
                ]
            finally:
                connection.close()
            self.assertEqual(statuses, ["released", "abandoned", "released"])

    def test_expired_waiting_ticket_cannot_starve_following_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clock = ManualClock()
            lease = self.make_lease(root, clock=clock)
            active = lease.acquire(0, 30)
            self.assertIsNotNone(active)

            connection = sqlite3.connect(root / "playwright-lease.sqlite3")
            try:
                connection.execute(
                    """
                    INSERT INTO playwright_lease_tickets(
                        token, status, enqueued_at, wait_until
                    ) VALUES ('crashed-waiter', 'waiting', ?, ?)
                    """,
                    (clock().isoformat(), clock().isoformat()),
                )
                connection.commit()
            finally:
                connection.close()

            self.assertTrue(lease.release(active))
            following = lease.acquire(0, 30)

            self.assertIsNotNone(following)
            self.assertTrue(lease.release(following))

    def test_waiters_claim_in_ticket_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lease = self.make_lease(Path(directory))
            active = lease.acquire(0, 30)
            self.assertIsNotNone(active)
            first_acquired = threading.Event()
            second_acquired = threading.Event()
            release_first = threading.Event()
            release_second = threading.Event()
            order: list[str] = []

            def claim(name: str, acquired: threading.Event, release: threading.Event) -> None:
                token = lease.acquire(2, 30, poll_interval_seconds=0.01)
                self.assertIsNotNone(token)
                order.append(name)
                acquired.set()
                release.wait(2)
                self.assertTrue(lease.release(token))

            first = threading.Thread(
                target=claim,
                args=("first", first_acquired, release_first),
            )
            second = threading.Thread(
                target=claim,
                args=("second", second_acquired, release_second),
            )
            first.start()
            time.sleep(0.05)
            second.start()
            time.sleep(0.05)
            self.assertTrue(lease.release(active))
            self.assertTrue(first_acquired.wait(1))
            self.assertFalse(second_acquired.is_set())
            release_first.set()
            self.assertTrue(second_acquired.wait(1))
            release_second.set()
            first.join(2)
            second.join(2)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(order, ["first", "second"])
