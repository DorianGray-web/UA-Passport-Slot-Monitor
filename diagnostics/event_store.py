"""SQLite source-of-truth store for observations, decisions, and outbox."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .domain import (
    DiagnosticDecision,
    DiagnosticSnapshotRequest,
    Observation,
    utc_now,
)


@dataclass(frozen=True, slots=True)
class PendingOutboxRecord:
    outbox_id: int
    decision_id: str
    request: DiagnosticSnapshotRequest
    attempt: int


class SQLiteEventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    provider_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS observations_provider_time
                    ON observations(provider_id, observed_at);

                CREATE TABLE IF NOT EXISTS diagnostic_decisions (
                    decision_id TEXT PRIMARY KEY,
                    observation_id TEXT NOT NULL UNIQUE,
                    outcome TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    FOREIGN KEY(observation_id)
                        REFERENCES observations(observation_id)
                );

                CREATE TABLE IF NOT EXISTS diagnostic_outbox (
                    outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    investigation_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempt INTEGER NOT NULL DEFAULT 0,
                    available_at TEXT NOT NULL,
                    delivered_at TEXT,
                    last_error TEXT,
                    FOREIGN KEY(decision_id)
                        REFERENCES diagnostic_decisions(decision_id)
                );
                """
            )

    def record(
        self,
        observation: Observation,
        decision: DiagnosticDecision,
        request: DiagnosticSnapshotRequest | None,
    ) -> None:
        """Atomically persist the fact, decision, and optional outbox command."""
        if decision.observation_id != observation.observation_id:
            raise ValueError("Decision must refer to the recorded observation.")
        if (decision.outcome == "ACCEPTED") != (request is not None):
            raise ValueError("Only ACCEPTED decisions require an outbox request.")
        if request is not None and (
            request.observation_id != observation.observation_id
            or request.investigation_id != decision.investigation_id
        ):
            raise ValueError("Outbox request identifiers do not match decision.")

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO observations(
                    observation_id, run_id, provider_id, observed_at, payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    observation.observation_id,
                    observation.run_id,
                    observation.provider_id,
                    observation.observed_at,
                    json.dumps(observation.to_dict(), separators=(",", ":")),
                ),
            )
            connection.execute(
                """
                INSERT INTO diagnostic_decisions(
                    decision_id, observation_id, outcome, decided_at, payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    decision.decision_id,
                    decision.observation_id,
                    decision.outcome,
                    decision.decided_at,
                    json.dumps(decision.to_dict(), separators=(",", ":")),
                ),
            )
            if request is not None:
                connection.execute(
                    """
                    INSERT INTO diagnostic_outbox(
                        decision_id, investigation_id, payload, available_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        decision.decision_id,
                        request.investigation_id,
                        json.dumps(request.to_dict(), separators=(",", ":")),
                        request.requested_at,
                    ),
                )

    def pending_outbox(self, limit: int = 10) -> list[PendingOutboxRecord]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT outbox_id, decision_id, payload, attempt
                FROM diagnostic_outbox
                WHERE status = 'pending' AND available_at <= ?
                ORDER BY outbox_id
                LIMIT ?
                """,
                (utc_now(), limit),
            ).fetchall()
        return [
            PendingOutboxRecord(
                outbox_id=row["outbox_id"],
                decision_id=row["decision_id"],
                request=DiagnosticSnapshotRequest(**json.loads(row["payload"])),
                attempt=row["attempt"],
            )
            for row in rows
        ]

    def mark_delivered(self, outbox_id: int) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE diagnostic_outbox
                SET status='delivered', delivered_at=?, last_error=NULL
                WHERE outbox_id=?
                """,
                (utc_now(), outbox_id),
            )

    def mark_retry(self, outbox_id: int, available_at: str, error: str) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE diagnostic_outbox
                SET attempt=attempt+1, available_at=?, last_error=?
                WHERE outbox_id=?
                """,
                (available_at, error[:500], outbox_id),
            )

    def observation_payloads(self) -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT payload FROM observations ORDER BY observed_at"
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]
