"""Crash-safe SQLite persistence for immutable notification delivery jobs."""

from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from .contracts import (
    NotificationAudience,
    NotificationDeliveryJob,
    NotificationEnvelope,
    NotificationPriority,
    parse_utc_timestamp,
    require_positive,
    require_text,
)


__architecture_layer__ = "queue"


PRIORITY_ORDER = {
    NotificationPriority.P0: 0,
    NotificationPriority.P1: 1,
    NotificationPriority.P2: 2,
    NotificationPriority.P3: 3,
}


class DeliveryJobStatus(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ClaimedDeliveryJob:
    job: NotificationDeliveryJob
    lease_token: str
    lease_owner: str
    lease_until: str
    attempt_count: int
    max_attempts: int


@dataclass(frozen=True)
class NotificationDeliveryState:
    job_id: str
    status: DeliveryJobStatus
    attempt_count: int
    max_attempts: int
    available_at: str
    lease_owner: str | None
    lease_token: str | None
    lease_until: str | None
    last_error_code: str | None
    completed_at: str | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamps must use UTC")
    return value.isoformat()


class SQLiteDeliveryJobStore:
    """Stores immutable jobs separately from mutable delivery state."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS notification_delivery_jobs (
                    job_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    decision_trace_id TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    priority_order INTEGER NOT NULL,
                    audience TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    destination_alias TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    dedup_key TEXT NOT NULL UNIQUE,
                    queued_at TEXT NOT NULL,
                    available_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notification_delivery_state (
                    job_id TEXT PRIMARY KEY REFERENCES notification_delivery_jobs(job_id),
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    available_at TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_token TEXT,
                    lease_until TEXT,
                    last_error_code TEXT,
                    completed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS notification_delivery_claim_idx
                    ON notification_delivery_state(status, available_at);
                CREATE TRIGGER IF NOT EXISTS notification_delivery_jobs_no_update
                    BEFORE UPDATE ON notification_delivery_jobs
                    BEGIN SELECT RAISE(ABORT, 'delivery jobs are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS notification_delivery_jobs_no_delete
                    BEFORE DELETE ON notification_delivery_jobs
                    BEGIN SELECT RAISE(ABORT, 'delivery jobs are immutable'); END;
                """
            )

    def enqueue(self, job: NotificationDeliveryJob, *, max_attempts: int = 3) -> bool:
        require_positive(max_attempts, "max_attempts")
        envelope_json = json.dumps(asdict(job.envelope), sort_keys=True, separators=(",", ":"))
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO notification_delivery_jobs (
                        job_id, event_id, decision_trace_id, priority, priority_order,
                        audience, channel, destination_alias, envelope_json, dedup_key,
                        queued_at, available_at, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.job_id, job.event_id, job.decision_trace_id,
                        job.priority.value, PRIORITY_ORDER[job.priority], job.audience.value,
                        job.channel, job.destination_alias, envelope_json, job.dedup_key,
                        job.queued_at, job.available_at, job.schema_version,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO notification_delivery_state (
                        job_id, status, attempt_count, max_attempts, available_at
                    ) VALUES (?, ?, 0, ?, ?)
                    """,
                    (job.job_id, DeliveryJobStatus.PENDING.value, max_attempts, job.available_at),
                )
                connection.commit()
                return True
            except sqlite3.IntegrityError:
                connection.rollback()
                row = connection.execute(
                    "SELECT job_id FROM notification_delivery_jobs WHERE dedup_key=?",
                    (job.dedup_key,),
                ).fetchone()
                if row is not None:
                    return False
                raise

    def claim(
        self,
        worker_id: str,
        lease_seconds: int,
        *,
        now: datetime | None = None,
    ) -> ClaimedDeliveryJob | None:
        require_text(worker_id, "worker_id")
        require_positive(lease_seconds, "lease_seconds")
        current = now or _utc_now()
        current_at = _timestamp(current)
        lease_until = _timestamp(current + timedelta(seconds=lease_seconds))
        lease_token = uuid4().hex
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE notification_delivery_state
                SET status=?, last_error_code='LEASE_EXPIRED_RETRY_LIMIT',
                    lease_owner=NULL, lease_token=NULL, lease_until=NULL
                WHERE status=? AND lease_until <= ?
                  AND attempt_count >= max_attempts
                """,
                (
                    DeliveryJobStatus.FAILED.value,
                    DeliveryJobStatus.CLAIMED.value,
                    current_at,
                ),
            )
            row = connection.execute(
                """
                SELECT j.*, s.attempt_count, s.max_attempts
                FROM notification_delivery_jobs AS j
                JOIN notification_delivery_state AS s USING (job_id)
                WHERE s.attempt_count < s.max_attempts
                  AND s.available_at <= ?
                  AND (
                    s.status = ? OR
                    (s.status = ? AND s.lease_until <= ?)
                  )
                ORDER BY j.priority_order, s.available_at, j.queued_at, j.job_id
                LIMIT 1
                """,
                (
                    current_at, DeliveryJobStatus.PENDING.value,
                    DeliveryJobStatus.CLAIMED.value, current_at,
                ),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            connection.execute(
                """
                UPDATE notification_delivery_state
                SET status=?, attempt_count=attempt_count+1, lease_owner=?,
                    lease_token=?, lease_until=?
                WHERE job_id=?
                """,
                (
                    DeliveryJobStatus.CLAIMED.value, worker_id, lease_token,
                    lease_until, row["job_id"],
                ),
            )
            connection.commit()
            return ClaimedDeliveryJob(
                job=self._job_from_row(row),
                lease_token=lease_token,
                lease_owner=worker_id,
                lease_until=lease_until,
                attempt_count=row["attempt_count"] + 1,
                max_attempts=row["max_attempts"],
            )

    def complete(
        self,
        job_id: str,
        lease_token: str,
        *,
        completed_at: datetime | None = None,
    ) -> bool:
        require_text(job_id, "job_id")
        require_text(lease_token, "lease_token")
        timestamp = _timestamp(completed_at or _utc_now())
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE notification_delivery_state
                SET status=?, completed_at=?, lease_owner=NULL,
                    lease_token=NULL, lease_until=NULL
                WHERE job_id=? AND status=? AND lease_token=?
                """,
                (
                    DeliveryJobStatus.COMPLETED.value, timestamp, job_id,
                    DeliveryJobStatus.CLAIMED.value, lease_token,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

    def fail(
        self,
        job_id: str,
        lease_token: str,
        error_code: str,
        retry_at: str,
    ) -> DeliveryJobStatus | None:
        require_text(job_id, "job_id")
        require_text(lease_token, "lease_token")
        require_text(error_code, "error_code")
        parse_utc_timestamp(retry_at, "retry_at")
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT attempt_count, max_attempts
                FROM notification_delivery_state
                WHERE job_id=? AND status=? AND lease_token=?
                """,
                (job_id, DeliveryJobStatus.CLAIMED.value, lease_token),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            terminal = row["attempt_count"] >= row["max_attempts"]
            status = DeliveryJobStatus.FAILED if terminal else DeliveryJobStatus.PENDING
            connection.execute(
                """
                UPDATE notification_delivery_state
                SET status=?, available_at=?, last_error_code=?, lease_owner=NULL,
                    lease_token=NULL, lease_until=NULL
                WHERE job_id=? AND status=? AND lease_token=?
                """,
                (
                    status.value, retry_at, error_code, job_id,
                    DeliveryJobStatus.CLAIMED.value, lease_token,
                ),
            )
            connection.commit()
            return status

    def state(self, job_id: str) -> NotificationDeliveryState | None:
        require_text(job_id, "job_id")
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM notification_delivery_state WHERE job_id=?", (job_id,)
            ).fetchone()
        if row is None:
            return None
        return NotificationDeliveryState(
            job_id=row["job_id"], status=DeliveryJobStatus(row["status"]),
            attempt_count=row["attempt_count"], max_attempts=row["max_attempts"],
            available_at=row["available_at"], lease_owner=row["lease_owner"],
            lease_token=row["lease_token"], lease_until=row["lease_until"],
            last_error_code=row["last_error_code"], completed_at=row["completed_at"],
        )

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> NotificationDeliveryJob:
        envelope_data = json.loads(row["envelope_json"])
        envelope = NotificationEnvelope(
            event_id=envelope_data["event_id"],
            priority=NotificationPriority(envelope_data["priority"]),
            audience=NotificationAudience(envelope_data["audience"]),
            title=envelope_data["title"], body=envelope_data["body"],
            official_url=envelope_data["official_url"],
            occurred_at=envelope_data["occurred_at"],
            schema_version=envelope_data["schema_version"],
        )
        return NotificationDeliveryJob(
            job_id=row["job_id"], event_id=row["event_id"],
            decision_trace_id=row["decision_trace_id"],
            priority=NotificationPriority(row["priority"]),
            audience=NotificationAudience(row["audience"]), channel=row["channel"],
            destination_alias=row["destination_alias"], envelope=envelope,
            dedup_key=row["dedup_key"], queued_at=row["queued_at"],
            available_at=row["available_at"], schema_version=row["schema_version"],
        )
