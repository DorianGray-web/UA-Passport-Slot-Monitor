"""Versioned SQLite schema migration runner for local engineering telemetry."""
from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sqlite3


MIGRATION_PACKAGE = "engineering_telemetry.migrations"


def migration_modules() -> list[str]:
    directory = Path(__file__).with_name("migrations")
    return sorted(path.stem for path in directory.glob("[0-9][0-9][0-9]_*.py"))


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Apply each numbered immutable migration once, in lexical order."""
    connection.execute("CREATE TABLE IF NOT EXISTS engineering_telemetry_schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    applied = {row[0] for row in connection.execute("SELECT version FROM engineering_telemetry_schema_migrations")}
    for name in migration_modules():
        version = name.split("_", 1)[0]
        if version in applied:
            continue
        migration = import_module(f"{MIGRATION_PACKAGE}.{name}")
        migration.up(connection)
        connection.execute("INSERT INTO engineering_telemetry_schema_migrations(version) VALUES (?)", (version,))
