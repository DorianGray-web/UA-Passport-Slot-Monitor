from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from notifications.contracts import (
    NotificationAudience,
    NotificationDeliveryJob,
    NotificationEnvelope,
    NotificationPriority,
)
from notifications.local_adapter import LocalFakeDeliveryAdapter
from notifications.queue import DeliveryJobStatus, SQLiteDeliveryJobStore
from notifications.worker import (
    DeliveryResult,
    DeliveryStatus,
    DeliveryWorkerOutcome,
    NotificationDeliveryWorker,
)


BASE_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)


def delivery_job(job_id: str) -> NotificationDeliveryJob:
    event_id = f"EVENT-{job_id}"
    envelope = NotificationEnvelope(
        event_id=event_id,
        priority=NotificationPriority.P1,
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
        priority=NotificationPriority.P1,
        audience=NotificationAudience.DEVELOPER,
        channel="test",
        destination_alias="DEVELOPER_TEST_DESTINATION",
        envelope=envelope,
        dedup_key=f"DEDUP-{job_id}",
        queued_at=BASE_TIME.isoformat(),
        available_at=BASE_TIME.isoformat(),
    )


class NotificationDeliveryWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = SQLiteDeliveryJobStore(
            Path(self.temporary.name) / "delivery-jobs.sqlite3"
        )

    def worker(self, *results: DeliveryResult) -> tuple[NotificationDeliveryWorker, LocalFakeDeliveryAdapter]:
        adapter = LocalFakeDeliveryAdapter(tuple(results))
        return (
            NotificationDeliveryWorker(
                self.store,
                adapter,
                worker_id="LOCAL_TEST_WORKER",
                lease_seconds=30,
                retry_delay_seconds=60,
            ),
            adapter,
        )

    def test_idle_worker_does_not_invoke_adapter(self) -> None:
        worker, adapter = self.worker(DeliveryResult(status=DeliveryStatus.SUCCESS))
        run = worker.run_once(now=BASE_TIME)
        self.assertEqual(run.outcome, DeliveryWorkerOutcome.IDLE)
        self.assertEqual(adapter.attempts, ())

    def test_successful_local_delivery_completes_persisted_job(self) -> None:
        job = delivery_job("worker-success")
        self.store.enqueue(job)
        initial_hash = hash(job)
        worker, adapter = self.worker(DeliveryResult(status=DeliveryStatus.SUCCESS))

        run = worker.run_once(now=BASE_TIME)

        self.assertEqual(run.outcome, DeliveryWorkerOutcome.COMPLETED)
        self.assertEqual(run.job_id, job.job_id)
        self.assertEqual(adapter.attempts, (job,))
        self.assertEqual(hash(job), initial_hash)
        self.assertEqual(hash(adapter.attempts[0]), initial_hash)
        state = self.store.state(job.job_id)
        assert state is not None
        self.assertEqual(state.status, DeliveryJobStatus.COMPLETED)
        self.assertEqual(state.attempt_count, 1)

    def test_failed_local_delivery_persists_retry_then_completion(self) -> None:
        job = delivery_job("worker-retry")
        self.store.enqueue(job, max_attempts=2)
        worker, adapter = self.worker(
            DeliveryResult(
                status=DeliveryStatus.RETRYABLE_FAILURE,
                reason="LOCAL_TRANSIENT",
            ),
            DeliveryResult(status=DeliveryStatus.SUCCESS),
        )

        first = worker.run_once(now=BASE_TIME)

        self.assertEqual(first.outcome, DeliveryWorkerOutcome.RETRY_SCHEDULED)
        state = self.store.state(job.job_id)
        assert state is not None
        self.assertEqual(state.status, DeliveryJobStatus.PENDING)
        self.assertEqual(state.last_error_code, "LOCAL_TRANSIENT")
        self.assertEqual(
            state.available_at,
            (BASE_TIME + timedelta(seconds=60)).isoformat(),
        )

        second = worker.run_once(now=BASE_TIME + timedelta(seconds=60))

        self.assertEqual(second.outcome, DeliveryWorkerOutcome.COMPLETED)
        state = self.store.state(job.job_id)
        assert state is not None
        self.assertEqual(state.status, DeliveryJobStatus.COMPLETED)
        self.assertEqual(state.attempt_count, 2)
        self.assertEqual(len(adapter.attempts), 2)

    def test_final_failed_local_delivery_is_terminal(self) -> None:
        job = delivery_job("worker-final-failure")
        self.store.enqueue(job, max_attempts=1)
        worker, _ = self.worker(
            DeliveryResult(
                status=DeliveryStatus.PERMANENT_FAILURE,
                reason="LOCAL_PERMANENT",
            )
        )

        run = worker.run_once(now=BASE_TIME)

        self.assertEqual(run.outcome, DeliveryWorkerOutcome.FAILED)
        state = self.store.state(job.job_id)
        assert state is not None
        self.assertEqual(state.status, DeliveryJobStatus.FAILED)
        self.assertEqual(state.last_error_code, "LOCAL_PERMANENT")


if __name__ == "__main__":
    unittest.main()
