"""Append-only SQLite persistence for local engineering telemetry."""
from __future__ import annotations
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from .contracts import EngineeringMetric, EngineeringSession
from .schema import apply_migrations

class SQLiteEngineeringTelemetryStore:
    """Stores immutable session and metric facts without network access."""
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
            apply_migrations(connection)
    def record_session(self, session: EngineeringSession) -> bool:
        with closing(self._connect()) as connection:
            try:
                connection.execute("INSERT INTO engineering_telemetry_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (session.session_id, session.recorded_at, session.provider, session.model, session.agent, json.dumps(session.skills), session.workflow_stage, session.duration_seconds, session.outcome.value, session.input_tokens, session.output_tokens, session.cached_tokens, session.estimated_cost_usd, session.schema_version))
                return True
            except sqlite3.IntegrityError:
                return False
    def record_metric(self, metric: EngineeringMetric) -> bool:
        with closing(self._connect()) as connection:
            try:
                connection.execute("INSERT INTO engineering_telemetry_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (metric.metric_id, metric.recorded_at, metric.source, metric.metric_name, metric.value, metric.unit, metric.session_id, metric.schema_version))
                return True
            except sqlite3.IntegrityError:
                return False
    def sessions_between(self, start: str, end: str) -> list[sqlite3.Row]:
        with closing(self._connect()) as connection:
            return connection.execute("SELECT * FROM engineering_telemetry_sessions WHERE recorded_at >= ? AND recorded_at < ? ORDER BY recorded_at, session_id", (start, end)).fetchall()
    def metrics_between(self, start: str, end: str) -> list[sqlite3.Row]:
        with closing(self._connect()) as connection:
            return connection.execute("SELECT * FROM engineering_telemetry_metrics WHERE recorded_at >= ? AND recorded_at < ? ORDER BY recorded_at, metric_id", (start, end)).fetchall()
