"""Backend-agnostic diagnostic queue contracts and implementations."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from .domain import (
    ClaimedJob,
    DiagnosticSnapshotRequest,
    DispatchReceipt,
    QueueJobError,
    utc_now,
)
from .investigator import InvestigationResult


PRIORITIES = {
    "SLOTS_AVAILABLE": 10,
    "CAPTCHA_REQUIRED": 20,
    "BLOCKED": 20,
    "UNKNOWN": 30,
    "HTML_STRUCTURE_CHANGED": 40,
    "QUEUE_SECTION_CHANGED": 40,
}
COOLDOWNS = {
    "SLOTS_AVAILABLE": 0,
    "CAPTCHA_REQUIRED": 5 * 60,
    "BLOCKED": 5 * 60,
    "UNKNOWN": 15 * 60,
    "HTML_STRUCTURE_CHANGED": 30 * 60,
    "QUEUE_SECTION_CHANGED": 30 * 60,
}


class DispatchTarget(Protocol):
    def dispatch(self, request: DiagnosticSnapshotRequest) -> DispatchReceipt:
        ...


class DiagnosticQueue(Protocol):
    def claim(self, worker_id: str, lease_seconds: int) -> ClaimedJob | None:
        ...

    def complete(
        self,
        investigation_id: str,
        lease_token: str,
        result: InvestigationResult,
    ) -> bool:
        ...

    def fail(
        self,
        investigation_id: str,
        lease_token: str,
        error: QueueJobError,
        retry_at: str | None,
    ) -> bool:
        ...


def priority_for(event: str) -> int:
    default = PRIORITIES.get(event, 50)
    return int(os.getenv(f"DIAGNOSTIC_PRIORITY_{event}", str(default)))


def cooldown_for(event: str) -> int:
    default = COOLDOWNS.get(event, 15 * 60)
    return max(
        0,
        int(os.getenv(f"DIAGNOSTIC_COOLDOWN_{event}", str(default))),
    )


def deduplication_key(request: DiagnosticSnapshotRequest) -> str:
    evidence = request.page_hash or "no-page-hash"
    return ":".join(
        (request.provider_id, request.mode, request.event, evidence)
    )


@dataclass
class _MemoryJob:
    request: DiagnosticSnapshotRequest
    priority: int
    dedup_key: str
    status: str = "queued"
    attempt: int = 0
    lease_token: str | None = None
    lease_until: str | None = None
    completed_at: str | None = None


class MemoryDiagnosticQueue(DispatchTarget, DiagnosticQueue):
    def __init__(self) -> None:
        self._jobs: dict[str, _MemoryJob] = {}
        self._lock = threading.Lock()

    def dispatch(self, request: DiagnosticSnapshotRequest) -> DispatchReceipt:
        key = deduplication_key(request)
        now = datetime.now(timezone.utc)
        with self._lock:
            existing = next(
                (job for job in self._jobs.values() if job.dedup_key == key),
                None,
            )
            if existing and existing.status in {"queued", "running", "retry_wait"}:
                return DispatchReceipt(
                    False, existing.request.investigation_id, "duplicate"
                )
            if existing and existing.completed_at:
                completed = datetime.fromisoformat(existing.completed_at)
                if now < completed + timedelta(seconds=cooldown_for(request.event)):
                    return DispatchReceipt(
                        False, existing.request.investigation_id, "cooldown"
                    )
            self._jobs[request.investigation_id] = _MemoryJob(
                request=request,
                priority=priority_for(request.event),
                dedup_key=key,
            )
        return DispatchReceipt(True, request.investigation_id, "accepted")

    def claim(self, worker_id: str, lease_seconds: int) -> ClaimedJob | None:
        del worker_id
        now = datetime.now(timezone.utc)
        with self._lock:
            eligible = [
                job
                for job in self._jobs.values()
                if job.status in {"queued", "retry_wait"}
                or (
                    job.status == "running"
                    and job.lease_until is not None
                    and datetime.fromisoformat(job.lease_until) <= now
                )
            ]
            if not eligible:
                return None
            job = min(
                eligible,
                key=lambda item: (item.priority, item.request.requested_at),
            )
            token = uuid.uuid4().hex
            lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
            job.status = "running"
            job.attempt += 1
            job.lease_token = token
            job.lease_until = lease_until
            return ClaimedJob(
                job.request.investigation_id,
                job.request,
                job.priority,
                job.attempt,
                token,
                lease_until,
            )

    def complete(
        self,
        investigation_id: str,
        lease_token: str,
        result: InvestigationResult,
    ) -> bool:
        del result
        with self._lock:
            job = self._jobs.get(investigation_id)
            if not job or job.status != "running" or job.lease_token != lease_token:
                return False
            job.status = "completed"
            job.completed_at = utc_now()
            return True

    def fail(
        self,
        investigation_id: str,
        lease_token: str,
        error: QueueJobError,
        retry_at: str | None,
    ) -> bool:
        with self._lock:
            job = self._jobs.get(investigation_id)
            if not job or job.status != "running" or job.lease_token != lease_token:
                return False
            job.status = "retry_wait" if error.retryable and retry_at else "failed"
            job.lease_until = retry_at
            job.lease_token = None
            return True


class SQLiteDiagnosticQueue(DispatchTarget, DiagnosticQueue):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path, timeout=10, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS diagnostic_jobs (
                    investigation_id TEXT PRIMARY KEY,
                    dedup_key TEXT NOT NULL,
                    event TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    request_payload TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    available_at TEXT NOT NULL,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    lease_owner TEXT,
                    lease_token TEXT,
                    lease_until TEXT,
                    completed_at TEXT,
                    result_payload TEXT,
                    last_error TEXT
                );
                CREATE INDEX IF NOT EXISTS diagnostic_jobs_claim
                    ON diagnostic_jobs(status, priority, available_at);
                CREATE INDEX IF NOT EXISTS diagnostic_jobs_dedup
                    ON diagnostic_jobs(dedup_key, completed_at);
                """
            )

    def dispatch(self, request: DiagnosticSnapshotRequest) -> DispatchReceipt:
        key = deduplication_key(request)
        now = datetime.now(timezone.utc)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                """
                SELECT investigation_id FROM diagnostic_jobs
                WHERE dedup_key=? AND status IN ('queued','running','retry_wait')
                LIMIT 1
                """,
                (key,),
            ).fetchone()
            if active:
                connection.commit()
                return DispatchReceipt(
                    False, active["investigation_id"], "duplicate"
                )
            previous = connection.execute(
                """
                SELECT investigation_id, completed_at FROM diagnostic_jobs
                WHERE dedup_key=? AND status='completed'
                ORDER BY completed_at DESC LIMIT 1
                """,
                (key,),
            ).fetchone()
            if previous and previous["completed_at"]:
                until = datetime.fromisoformat(previous["completed_at"]) + timedelta(
                    seconds=cooldown_for(request.event)
                )
                if now < until:
                    connection.commit()
                    return DispatchReceipt(
                        False, previous["investigation_id"], "cooldown"
                    )
            connection.execute(
                """
                INSERT OR IGNORE INTO diagnostic_jobs(
                    investigation_id, dedup_key, event, priority, status,
                    request_payload, requested_at, available_at
                ) VALUES (?, ?, ?, ?, 'queued', ?, ?, ?)
                """,
                (
                    request.investigation_id,
                    key,
                    request.event,
                    priority_for(request.event),
                    json.dumps(request.to_dict(), separators=(",", ":")),
                    request.requested_at,
                    request.requested_at,
                ),
            )
            inserted = connection.total_changes > 0
            connection.commit()
        return DispatchReceipt(
            inserted,
            request.investigation_id,
            "accepted" if inserted else "duplicate",
        )

    def claim(self, worker_id: str, lease_seconds: int) -> ClaimedJob | None:
        now = datetime.now(timezone.utc)
        now_text = now.isoformat()
        lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
        token = uuid.uuid4().hex
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT * FROM diagnostic_jobs
                WHERE (
                    status IN ('queued','retry_wait') AND available_at <= ?
                ) OR (
                    status='running' AND lease_until <= ?
                )
                ORDER BY priority ASC, requested_at ASC
                LIMIT 1
                """,
                (now_text, now_text),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            connection.execute(
                """
                UPDATE diagnostic_jobs
                SET status='running', attempt=attempt+1, lease_owner=?,
                    lease_token=?, lease_until=?
                WHERE investigation_id=?
                """,
                (worker_id, token, lease_until, row["investigation_id"]),
            )
            connection.commit()
        return ClaimedJob(
            row["investigation_id"],
            DiagnosticSnapshotRequest(**json.loads(row["request_payload"])),
            row["priority"],
            row["attempt"] + 1,
            token,
            lease_until,
        )

    def complete(
        self,
        investigation_id: str,
        lease_token: str,
        result: InvestigationResult,
    ) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE diagnostic_jobs
                SET status='completed', completed_at=?, result_payload=?,
                    lease_owner=NULL, lease_token=NULL, lease_until=NULL
                WHERE investigation_id=? AND status='running' AND lease_token=?
                """,
                (
                    utc_now(),
                    json.dumps(
                        {
                            "schema_version": 1,
                            "success": result.success,
                            "investigation_id": result.investigation_id,
                            "exit_code": result.exit_code,
                            "output_directory": result.output_directory,
                            "summary": result.summary,
                        },
                        separators=(",", ":"),
                    ),
                    investigation_id,
                    lease_token,
                ),
            )
            return cursor.rowcount == 1

    def fail(
        self,
        investigation_id: str,
        lease_token: str,
        error: QueueJobError,
        retry_at: str | None,
    ) -> bool:
        retry = error.retryable and retry_at is not None
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE diagnostic_jobs
                SET status=?, available_at=?, last_error=?, lease_owner=NULL,
                    lease_token=NULL, lease_until=NULL
                WHERE investigation_id=? AND status='running' AND lease_token=?
                """,
                (
                    "retry_wait" if retry else "failed",
                    retry_at or utc_now(),
                    f"{error.category}: {error.message}"[:500],
                    investigation_id,
                    lease_token,
                ),
            )
            return cursor.rowcount == 1
