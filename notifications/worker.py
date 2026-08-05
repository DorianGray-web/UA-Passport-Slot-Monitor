"""Local, one-job delivery worker without runtime or network integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import re
from typing import Protocol

from .contracts import NotificationDeliveryJob, require_positive, require_text
from .queue import DeliveryJobStatus, SQLiteDeliveryJobStore


__architecture_layer__ = "adapter"


ERROR_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


class DeliveryStatus(str, Enum):
    SUCCESS = "SUCCESS"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"


@dataclass(frozen=True)
class DeliveryResult:
    """Small, sanitized result returned by a delivery adapter."""

    status: DeliveryStatus
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status is DeliveryStatus.SUCCESS:
            if self.reason is not None:
                raise ValueError("successful delivery must not include a reason")
            return
        if not isinstance(self.reason, str) or ERROR_CODE_PATTERN.fullmatch(self.reason) is None:
            raise ValueError("failed delivery requires a sanitized reason")


class LocalDeliveryAdapter(Protocol):
    """Adapter boundary; implementations receive no Observation or provider state."""

    def deliver(
        self,
        job: NotificationDeliveryJob,
    ) -> DeliveryResult:
        """Attempt one local delivery and return a sanitized outcome."""


class DeliveryWorkerOutcome(str, Enum):
    IDLE = "IDLE"
    COMPLETED = "COMPLETED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DeliveryWorkerRun:
    outcome: DeliveryWorkerOutcome
    job_id: str | None = None
    error_code: str | None = None


class NotificationDeliveryWorker:
    """Claims and settles one persisted job using a local adapter.

    This worker is deliberately caller-driven: it has no scheduler, background
    loop, runtime hook, network code, or knowledge of notifications' origin.
    """

    def __init__(
        self,
        store: SQLiteDeliveryJobStore,
        adapter: LocalDeliveryAdapter,
        *,
        worker_id: str,
        lease_seconds: int = 30,
        retry_delay_seconds: int = 60,
    ) -> None:
        require_text(worker_id, "worker_id")
        require_positive(lease_seconds, "lease_seconds")
        require_positive(retry_delay_seconds, "retry_delay_seconds")
        self.store = store
        self.adapter = adapter
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self.retry_delay_seconds = retry_delay_seconds

    def run_once(self, *, now: datetime | None = None) -> DeliveryWorkerRun:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() != timedelta(0):
            raise ValueError("now must use UTC")

        claimed = self.store.claim(
            self.worker_id,
            self.lease_seconds,
            now=current,
        )
        if claimed is None:
            return DeliveryWorkerRun(DeliveryWorkerOutcome.IDLE)

        result = self.adapter.deliver(claimed.job)
        if result.status is DeliveryStatus.SUCCESS:
            if not self.store.complete(
                claimed.job.job_id,
                claimed.lease_token,
                completed_at=current,
            ):
                return DeliveryWorkerRun(
                    DeliveryWorkerOutcome.FAILED,
                    job_id=claimed.job.job_id,
                    error_code="LEASE_LOST",
                )
            return DeliveryWorkerRun(
                DeliveryWorkerOutcome.COMPLETED,
                job_id=claimed.job.job_id,
            )

        assert result.reason is not None
        retry_at = (current + timedelta(seconds=self.retry_delay_seconds)).isoformat()
        status = self.store.fail(
            claimed.job.job_id,
            claimed.lease_token,
            result.reason,
            retry_at,
            retry=result.status is DeliveryStatus.RETRYABLE_FAILURE,
        )
        outcome = (
            DeliveryWorkerOutcome.RETRY_SCHEDULED
            if status is DeliveryJobStatus.PENDING
            else DeliveryWorkerOutcome.FAILED
        )
        return DeliveryWorkerRun(
            outcome,
            job_id=claimed.job.job_id,
            error_code=result.reason,
        )
