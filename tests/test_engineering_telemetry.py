from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing

from engineering_telemetry import AuditPeriod, EngineeringMetric, EngineeringSession, SessionOutcome, SQLiteEngineeringTelemetryStore, render_audit_report


class EngineeringTelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.store = SQLiteEngineeringTelemetryStore(Path(self.directory.name) / "telemetry.sqlite3")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def session(self, session_id: str = "session-1", at: str = "2026-08-04T10:00:00+00:00", outcome: SessionOutcome = SessionOutcome.COMPLETED) -> EngineeringSession:
        return EngineeringSession(session_id, at, "openai", "gpt-5", "codex", ("architecture",), "implementation", 120, outcome, 100, 50, 10, 0.02)

    def test_records_are_immutable_and_duplicate_safe(self) -> None:
        self.assertTrue(self.store.record_session(self.session()))
        self.assertFalse(self.store.record_session(self.session()))
        with self.assertRaises(sqlite3.DatabaseError):
            with closing(sqlite3.connect(self.store.path)) as connection:
                connection.execute("UPDATE engineering_telemetry_sessions SET provider='other'")

    def test_metric_is_generic_and_links_to_existing_session(self) -> None:
        self.store.record_session(self.session())
        metric = EngineeringMetric("metric-1", "2026-08-04T10:05:00+00:00", "ci", "duration_seconds", 42, "seconds", "session-1")
        self.assertTrue(self.store.record_metric(metric))
        self.assertFalse(self.store.record_metric(metric))

    def test_initial_schema_migration_is_recorded_once(self) -> None:
        with closing(sqlite3.connect(self.store.path)) as connection:
            versions = [row[0] for row in connection.execute("SELECT version FROM engineering_telemetry_schema_migrations")]
        self.assertEqual(["001"], versions)
        SQLiteEngineeringTelemetryStore(self.store.path)
        with closing(sqlite3.connect(self.store.path)) as connection:
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM engineering_telemetry_schema_migrations").fetchone()[0])

    def test_contract_rejects_sensitive_or_mutable_data(self) -> None:
        with self.assertRaises(ValueError):
            EngineeringSession("session-2", "2026-08-04T10:00:00+00:00", "openai", "gpt-5", "codex", ["architecture"], "prompt-review", 1, SessionOutcome.COMPLETED)

    def test_daily_report_uses_only_aggregate_facts(self) -> None:
        self.store.record_session(self.session())
        self.store.record_session(self.session("session-2", "2026-08-04T11:00:00+00:00", SessionOutcome.FAILED))
        report = render_audit_report(self.store, AuditPeriod.DAILY, datetime(2026, 8, 4, tzinfo=timezone.utc))
        self.assertIn("Sessions: 2", report)
        self.assertIn("Input tokens: 200", report)
        self.assertIn("Completion rate: 50.0%", report)
        self.assertIn("Review failed sessions", report)
        self.assertNotIn("prompt-review", report)

    def test_weekly_and_monthly_boundaries_are_deterministic(self) -> None:
        self.store.record_session(self.session())
        weekly = render_audit_report(self.store, AuditPeriod.WEEKLY, datetime(2026, 8, 4, tzinfo=timezone.utc))
        monthly = render_audit_report(self.store, AuditPeriod.MONTHLY, datetime(2026, 8, 4, tzinfo=timezone.utc))
        self.assertIn("Start (UTC): `2026-08-03T00:00:00+00:00`", weekly)
        self.assertIn("Start (UTC): `2026-08-01T00:00:00+00:00`", monthly)


if __name__ == "__main__":
    unittest.main()
