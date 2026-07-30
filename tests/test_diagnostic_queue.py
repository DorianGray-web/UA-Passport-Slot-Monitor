from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from diagnostics.domain import DiagnosticSnapshotRequest
from diagnostics.investigator import InvestigationResult
from diagnostics.queue import MemoryDiagnosticQueue, SQLiteDiagnosticQueue


def request(
    investigation_id: str,
    event: str,
    *,
    provider: str = "dp-document-berlin",
    mode: str = "research",
    page_hash: str = "hash",
) -> DiagnosticSnapshotRequest:
    return DiagnosticSnapshotRequest(
        investigation_id=investigation_id,
        observation_id=f"OBS-{investigation_id}",
        run_id="RUN-test",
        provider_id=provider,
        url="https://example.test/queue",
        event=event,
        reason="test",
        mode=mode,
        page_hash=page_hash,
        requested_at=datetime.now(timezone.utc).isoformat(),
    )


def result(investigation_id: str) -> InvestigationResult:
    return InvestigationResult(True, investigation_id, 0, "output", "ok")


class QueueContractMixin:
    queue: MemoryDiagnosticQueue | SQLiteDiagnosticQueue

    def test_priority_order(self) -> None:
        self.queue.dispatch(request("INV-low", "HTML_STRUCTURE_CHANGED"))
        self.queue.dispatch(
            request("INV-high", "SLOTS_AVAILABLE", page_hash="slots")
        )
        claimed = self.queue.claim("worker", 300)
        assert claimed is not None
        self.assertEqual(claimed.investigation_id, "INV-high")

    def test_active_duplicate_is_suppressed(self) -> None:
        first = self.queue.dispatch(request("INV-first", "BLOCKED"))
        duplicate = self.queue.dispatch(request("INV-second", "BLOCKED"))
        self.assertTrue(first.accepted)
        self.assertFalse(duplicate.accepted)
        self.assertEqual(duplicate.reason, "duplicate")
        self.assertEqual(duplicate.investigation_id, "INV-first")

    def test_mode_participates_in_deduplication(self) -> None:
        self.queue.dispatch(request("INV-research", "BLOCKED", mode="research"))
        production = self.queue.dispatch(
            request("INV-production", "BLOCKED", mode="production")
        )
        self.assertTrue(production.accepted)

    def test_stale_lease_cannot_complete_reclaimed_job(self) -> None:
        self.queue.dispatch(request("INV-lease", "UNKNOWN"))
        first = self.queue.claim("worker-a", -1)
        assert first is not None
        second = self.queue.claim("worker-b", 300)
        assert second is not None
        self.assertEqual(first.investigation_id, second.investigation_id)
        self.assertFalse(
            self.queue.complete(
                first.investigation_id,
                first.lease_token,
                result(first.investigation_id),
            )
        )
        self.assertTrue(
            self.queue.complete(
                second.investigation_id,
                second.lease_token,
                result(second.investigation_id),
            )
        )


class MemoryDiagnosticQueueTests(QueueContractMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.queue = MemoryDiagnosticQueue()


class SQLiteDiagnosticQueueTests(QueueContractMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.queue = SQLiteDiagnosticQueue(
            Path(self.temporary.name) / "queue.sqlite3"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_completed_job_respects_cooldown(self) -> None:
        queued = request("INV-cooldown", "HTML_STRUCTURE_CHANGED")
        self.queue.dispatch(queued)
        claimed = self.queue.claim("worker", 300)
        assert claimed is not None
        self.queue.complete(
            claimed.investigation_id,
            claimed.lease_token,
            result(claimed.investigation_id),
        )
        repeated = self.queue.dispatch(
            request("INV-repeat", "HTML_STRUCTURE_CHANGED")
        )
        self.assertFalse(repeated.accepted)
        self.assertEqual(repeated.reason, "cooldown")

    def test_expired_running_job_is_reclaimed_after_restart(self) -> None:
        self.queue.dispatch(request("INV-recovery", "BLOCKED"))
        first = self.queue.claim("worker-a", 300)
        assert first is not None
        with closing(sqlite3.connect(self.queue.path)) as connection:
            connection.execute(
                "UPDATE diagnostic_jobs SET lease_until=? WHERE investigation_id=?",
                (
                    (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                    first.investigation_id,
                ),
            )
            connection.commit()
        reopened = SQLiteDiagnosticQueue(self.queue.path)
        recovered = reopened.claim("worker-b", 300)
        assert recovered is not None
        self.assertEqual(recovered.investigation_id, first.investigation_id)
        self.assertEqual(recovered.attempt, 2)


if __name__ == "__main__":
    unittest.main()
