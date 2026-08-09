from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright_execution_budget import PlaywrightExecutionBudget


class ManualClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)

    def monotonic(self) -> float:
        origin = datetime(2026, 8, 9, tzinfo=timezone.utc)
        return (self.now - origin).total_seconds()


class PlaywrightExecutionBudgetTests(unittest.TestCase):
    def make_budget(
        self,
        root: Path,
        clock: ManualClock,
        *,
        interval_seconds: float,
    ) -> PlaywrightExecutionBudget:
        return PlaywrightExecutionBudget(
            root / "playwright-execution-budget.sqlite3",
            clock=clock,
            monotonic=clock.monotonic,
            sleeper=clock.advance,
            random_uniform=lambda minimum, maximum: interval_seconds,
        )

    def test_budget_persists_next_start_without_provider_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clock = ManualClock()
            budget = self.make_budget(root, clock, interval_seconds=75)

            next_start = budget.defer_next(
                min_interval_seconds=60,
                max_interval_seconds=120,
            )

            self.assertEqual(
                next_start,
                datetime(2026, 8, 9, 0, 1, 15, tzinfo=timezone.utc),
            )
            connection = sqlite3.connect(
                root / "playwright-execution-budget.sqlite3"
            )
            try:
                columns = [
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(playwright_execution_budget)"
                    )
                ]
            finally:
                connection.close()
            self.assertEqual(columns, ["singleton", "next_start_at"])

    def test_wait_returns_deterministic_budget_wait_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = ManualClock()
            budget = self.make_budget(
                Path(directory),
                clock,
                interval_seconds=75,
            )
            budget.defer_next(
                min_interval_seconds=60,
                max_interval_seconds=120,
            )

            waited = budget.wait_until_allowed(
                90,
                poll_interval_seconds=15,
            )

            self.assertEqual(waited, 75)

    def test_wait_timeout_does_not_change_persisted_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = ManualClock()
            budget = self.make_budget(
                Path(directory),
                clock,
                interval_seconds=120,
            )
            expected = budget.defer_next(
                min_interval_seconds=60,
                max_interval_seconds=120,
            )

            self.assertIsNone(
                budget.wait_until_allowed(30, poll_interval_seconds=10)
            )
            clock.advance(90)
            self.assertEqual(budget.wait_until_allowed(0), 0)
            self.assertEqual(expected, clock())
