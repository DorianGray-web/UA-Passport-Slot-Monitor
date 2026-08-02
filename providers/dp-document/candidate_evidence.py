"""Local-only candidate evidence governed by ADR-0011."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from provider_protocol import CandidateQueueForm


class CandidateEvidenceStore:
    """Persist sanitized research material outside domain state."""

    def __init__(self, root: Path, provider_id: str) -> None:
        self.root = root
        self.provider_id = provider_id
        self.artifact_path = root / "candidate-services.json"
        self.probe_state_path = root / "probe-state.json"

    def write_candidate(
        self,
        *,
        observed_at: str,
        transport: str,
        page_hash: str,
        candidate: CandidateQueueForm,
    ) -> Path:
        payload = {
            "schema_version": 1,
            "provider_id": self.provider_id,
            "observed_at": observed_at,
            "transport": transport,
            "page_hash": page_hash,
            "service_center_id": candidate.service_center_id,
            "options": [asdict(option) for option in candidate.options],
            "date_selector_found": candidate.date_selector_found,
            "time_selector_found": candidate.time_selector_found,
        }
        self._write_json(self.artifact_path, payload)
        return self.artifact_path

    def should_probe(
        self,
        *,
        transport: str,
        page_hash: str,
        cooldown_seconds: int,
    ) -> bool:
        key = [self.provider_id, transport, page_hash]
        state = self._read_json(self.probe_state_path)
        if state.get("probe_key") == key:
            return False
        observed_at = state.get("observed_at")
        if isinstance(observed_at, str):
            try:
                previous = datetime.fromisoformat(observed_at)
                elapsed = (datetime.now(timezone.utc) - previous).total_seconds()
                if elapsed < cooldown_seconds:
                    return False
            except ValueError:
                pass
        return True

    def mark_probe(self, *, transport: str, page_hash: str) -> None:
        self._write_json(
            self.probe_state_path,
            {
                "schema_version": 1,
                "provider_id": self.provider_id,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "probe_key": [self.provider_id, transport, page_hash],
            },
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, object]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
