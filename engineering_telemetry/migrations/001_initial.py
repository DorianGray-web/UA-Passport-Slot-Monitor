"""Initial append-only engineering telemetry tables."""
from __future__ import annotations
import sqlite3

def up(connection: sqlite3.Connection) -> None:
    connection.executescript("""
        CREATE TABLE engineering_telemetry_sessions (
            session_id TEXT PRIMARY KEY, recorded_at TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, agent TEXT NOT NULL, skills_json TEXT NOT NULL, workflow_stage TEXT NOT NULL, duration_seconds INTEGER NOT NULL, outcome TEXT NOT NULL, input_tokens INTEGER, output_tokens INTEGER, cached_tokens INTEGER, estimated_cost_usd REAL, schema_version INTEGER NOT NULL);
        CREATE TABLE engineering_telemetry_metrics (
            metric_id TEXT PRIMARY KEY, recorded_at TEXT NOT NULL, source TEXT NOT NULL, metric_name TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL, session_id TEXT, schema_version INTEGER NOT NULL, FOREIGN KEY(session_id) REFERENCES engineering_telemetry_sessions(session_id));
        CREATE INDEX engineering_telemetry_sessions_at_idx ON engineering_telemetry_sessions(recorded_at);
        CREATE INDEX engineering_telemetry_metrics_at_idx ON engineering_telemetry_metrics(recorded_at);
        CREATE TRIGGER engineering_telemetry_sessions_no_update BEFORE UPDATE ON engineering_telemetry_sessions BEGIN SELECT RAISE(ABORT, 'engineering sessions are immutable'); END;
        CREATE TRIGGER engineering_telemetry_sessions_no_delete BEFORE DELETE ON engineering_telemetry_sessions BEGIN SELECT RAISE(ABORT, 'engineering sessions are immutable'); END;
        CREATE TRIGGER engineering_telemetry_metrics_no_update BEFORE UPDATE ON engineering_telemetry_metrics BEGIN SELECT RAISE(ABORT, 'engineering metrics are immutable'); END;
        CREATE TRIGGER engineering_telemetry_metrics_no_delete BEFORE DELETE ON engineering_telemetry_metrics BEGIN SELECT RAISE(ABORT, 'engineering metrics are immutable'); END;
    """)
