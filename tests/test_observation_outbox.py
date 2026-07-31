from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

from diagnostics.dispatcher import DiagnosticDispatcher
from diagnostics.domain import Observation, RequestTraceEntry
from diagnostics.event_store import SQLiteEventStore
from diagnostics.monitoring import ObservationService
from diagnostics.queue import MemoryDiagnosticQueue


class ObservationOutboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "events.sqlite3"
        self.store = SQLiteEventStore(self.database)
        self.service = ObservationService(self.store, run_id="RUN-test")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def record(self, events: list[str]):
        return self.service.record(
            provider_id="dp-document-berlin",
            url="https://example.test/queue",
            observed_at="2026-07-30T16:39:36+00:00",
            transport="http",
            state="NO_SLOTS",
            duration_ms=842,
            http_status=200,
            page_hash="abc",
            html_changed=True,
            classifier_reason="changed",
            error_category=None,
            diagnostic_events=events,
            mode="research",
        )

    def test_observation_decision_and_outbox_are_atomic(self) -> None:
        with patch.dict(
            "os.environ", {"DIAGNOSTIC_QUEUE_ENABLED": "true"}, clear=False
        ):
            recorded = self.record(["HTML_STRUCTURE_CHANGED"])

        with closing(sqlite3.connect(self.database)) as connection:
            observation_count = connection.execute(
                "SELECT COUNT(*) FROM observations"
            ).fetchone()[0]
            decision_count = connection.execute(
                "SELECT COUNT(*) FROM diagnostic_decisions"
            ).fetchone()[0]
            outbox_count = connection.execute(
                "SELECT COUNT(*) FROM diagnostic_outbox"
            ).fetchone()[0]
        self.assertEqual((observation_count, decision_count, outbox_count), (1, 1, 1))
        self.assertEqual(recorded.decision.outcome, "ACCEPTED")
        self.assertEqual(recorded.observation.schema_version, 3)

    def test_not_required_decision_has_no_outbox_record(self) -> None:
        recorded = self.record([])
        self.assertEqual(recorded.decision.outcome, "NOT_REQUIRED")
        self.assertEqual(self.store.pending_outbox(), [])

    def test_dispatcher_delivers_outbox_without_backend_knowledge(self) -> None:
        with patch.dict(
            "os.environ", {"DIAGNOSTIC_QUEUE_ENABLED": "true"}, clear=False
        ):
            recorded = self.record(["BLOCKED"])
        queue = MemoryDiagnosticQueue()
        delivered = DiagnosticDispatcher(self.store, queue).dispatch_pending()
        claimed = queue.claim("worker", 300)
        assert claimed is not None

        self.assertEqual(delivered, 1)
        self.assertEqual(
            claimed.investigation_id,
            recorded.decision.investigation_id,
        )
        self.assertEqual(self.store.pending_outbox(), [])

    def test_observation_payload_is_source_of_truth(self) -> None:
        self.record([])
        payload = self.store.observation_payloads()[0]
        self.assertEqual(payload["provider_id"], "dp-document-berlin")
        self.assertEqual(payload["duration_ms"], 842)
        self.assertNotIn("notification_sent", payload)
        self.assertNotIn("diagnostics_requested", payload)

    def test_observation_and_trace_contracts_exclude_sensitive_payloads(self) -> None:
        observation_fields = {field.name for field in fields(Observation)}
        trace_fields = {field.name for field in fields(RequestTraceEntry)}
        forbidden = {
            "headers",
            "cookies",
            "body",
            "payload",
            "csrf",
            "csrf_token",
            "captcha",
            "fingerprint",
            "authorization",
        }
        self.assertTrue(observation_fields.isdisjoint(forbidden))
        self.assertTrue(trace_fields.isdisjoint(forbidden))
        self.assertEqual(
            trace_fields,
            {
                "method",
                "operation",
                "status_code",
                "duration_ms",
                "response_bytes",
                "attempt",
                "transport",
            },
        )


if __name__ == "__main__":
    unittest.main()
