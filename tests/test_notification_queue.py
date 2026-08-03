from __future__ import annotations

from contextlib import closing
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import sqlite3
from pathlib import Path
import tempfile
import unittest

from notifications.contracts import (
    NotificationAudience,
    NotificationDeliveryJob,
    NotificationEnvelope,
    NotificationPriority,
)
from notifications.queue import DeliveryJobStatus, SQLiteDeliveryJobStore


BASE_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)


def delivery_job(
    job_id: str,
    *,
    priority: NotificationPriority = NotificationPriority.P1,
    dedup_key: str | None = None,
    available_at: datetime = BASE_TIME,
) -> NotificationDeliveryJob:
    event_id = f"EVENT-{job_id}"
    envelope = NotificationEnvelope(
        event_id=event_id,
        priority=priority,
        audience=NotificationAudience.DEVELOPER,
        title="Availability confirmed",
        body="Public availability was confirmed.",
        official_url="https://example.invalid/public-queue",
        occurred_at=BASE_TIME.isoformat(),
    )
    return NotificationDeliveryJob(
        job_id=job_id,
        event_id=event_id,
        decision_trace_id=f"TRACE-{job_id}",
        priority=priority,
        audience=NotificationAudience.DEVELOPER,
        channel="test",
        destination_alias="DEVELOPER_TEST_DESTINATION",
        envelope=envelope,
        dedup_key=dedup_key or f"DEDUP-{job_id}",
        queued_at=BASE_TIME.isoformat(),
        available_at=available_at.isoformat(),
    )


class SQLiteDeliveryJobStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "delivery-jobs.sqlite3"
        self.store = SQLiteDeliveryJobStore(self.database)

    def test_job_contract_and_persisted_job_are_immutable(self) -> None:
        job = delivery_job("immutable")
        with self.assertRaises(FrozenInstanceError):
            job.channel = "changed"  # type: ignore[misc]
        self.assertTrue(self.store.enqueue(job))
        with closing(sqlite3.connect(self.database)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE notification_delivery_jobs SET channel='changed' WHERE job_id=?",
                    (job.job_id,),
                )

    def test_enqueue_is_idempotent_by_caller_supplied_dedup_key(self) -> None:
        first = delivery_job("first", dedup_key="LOGICAL-EVENT-1")
        duplicate = delivery_job("duplicate", dedup_key="LOGICAL-EVENT-1")
        self.assertTrue(self.store.enqueue(first))
        self.assertFalse(self.store.enqueue(duplicate))
        self.assertIsNone(self.store.state(duplicate.job_id))

    def test_claim_orders_already_classified_priority(self) -> None:
        self.store.enqueue(delivery_job("p2", priority=NotificationPriority.P2))
        self.store.enqueue(delivery_job("p0", priority=NotificationPriority.P0))
        claimed = self.store.claim("worker", 30, now=BASE_TIME)
        self.assertIsNotNone(claimed)
        assert claimed is not None
        self.assertEqual(claimed.job.job_id, "p0")
        self.assertEqual(claimed.job.priority, NotificationPriority.P0)

    def test_complete_requires_current_lease_token(self) -> None:
        self.store.enqueue(delivery_job("complete"))
        claimed = self.store.claim("worker", 30, now=BASE_TIME)
        assert claimed is not None
        self.assertFalse(
            self.store.complete("complete", "stale-token", completed_at=BASE_TIME)
        )
        self.assertTrue(
            self.store.complete(
                "complete", claimed.lease_token, completed_at=BASE_TIME
            )
        )
        state = self.store.state("complete")
        assert state is not None
        self.assertEqual(state.status, DeliveryJobStatus.COMPLETED)
        self.assertIsNone(state.lease_token)

    def test_expired_lease_is_reclaimed_and_stale_completion_is_rejected(self) -> None:
        self.store.enqueue(delivery_job("reclaim"))
        first = self.store.claim("worker-1", 30, now=BASE_TIME)
        assert first is not None
        second = self.store.claim(
            "worker-2", 30, now=BASE_TIME + timedelta(seconds=31)
        )
        assert second is not None
        self.assertNotEqual(first.lease_token, second.lease_token)
        self.assertEqual(second.attempt_count, 2)
        self.assertFalse(
            self.store.complete(
                "reclaim", first.lease_token,
                completed_at=BASE_TIME + timedelta(seconds=32),
            )
        )
        self.assertTrue(
            self.store.complete(
                "reclaim", second.lease_token,
                completed_at=BASE_TIME + timedelta(seconds=32),
            )
        )

    def test_fail_retries_until_persisted_attempt_bound(self) -> None:
        self.store.enqueue(delivery_job("retry"), max_attempts=2)
        first = self.store.claim("worker", 30, now=BASE_TIME)
        assert first is not None
        retry_at = (BASE_TIME + timedelta(minutes=1)).isoformat()
        self.assertEqual(
            self.store.fail("retry", first.lease_token, "TRANSIENT", retry_at),
            DeliveryJobStatus.PENDING,
        )
        second = self.store.claim(
            "worker", 30, now=BASE_TIME + timedelta(minutes=1)
        )
        assert second is not None
        self.assertEqual(
            self.store.fail(
                "retry", second.lease_token, "TRANSIENT",
                (BASE_TIME + timedelta(minutes=2)).isoformat(),
            ),
            DeliveryJobStatus.FAILED,
        )
        state = self.store.state("retry")
        assert state is not None
        self.assertEqual(state.attempt_count, 2)
        self.assertEqual(state.max_attempts, 2)
        self.assertIsNone(
            self.store.claim("worker", 30, now=BASE_TIME + timedelta(minutes=3))
        )

    def test_expired_final_lease_becomes_terminal_instead_of_stalling(self) -> None:
        self.store.enqueue(delivery_job("expired-final"), max_attempts=1)
        claimed = self.store.claim("worker", 30, now=BASE_TIME)
        self.assertIsNotNone(claimed)
        self.assertIsNone(
            self.store.claim("worker-2", 30, now=BASE_TIME + timedelta(seconds=31))
        )
        state = self.store.state("expired-final")
        assert state is not None
        self.assertEqual(state.status, DeliveryJobStatus.FAILED)
        self.assertEqual(state.last_error_code, "LEASE_EXPIRED_RETRY_LIMIT")
        self.assertIsNone(state.lease_token)

    def test_future_job_is_not_claimed_early(self) -> None:
        future = BASE_TIME + timedelta(minutes=5)
        self.store.enqueue(delivery_job("future", available_at=future))
        self.assertIsNone(self.store.claim("worker", 30, now=BASE_TIME))
        claimed = self.store.claim("worker", 30, now=future)
        self.assertIsNotNone(claimed)


if __name__ == "__main__":
    unittest.main()
