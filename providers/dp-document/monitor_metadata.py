from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class MonitoringMetadata:
    timestamp: str
    provider: str
    state: str
    transport: str
    diagnostics: bool
    html_changed: bool
    response_time_ms: int
    http_status: int | None


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_metadata(path: Path, record: MonitoringMetadata) -> None:
    """Append one analysis-safe observation as a JSON Lines record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        json.dump(asdict(record), stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")
