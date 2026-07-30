"""Application service connecting immutable observations to diagnostic policy."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .domain import (
    DiagnosticDecision,
    DiagnosticSnapshotRequest,
    Observation,
    RequestTraceEntry,
    make_decision_id,
    make_investigation_id,
    make_observation_id,
    utc_now,
)
from .event_store import SQLiteEventStore
from .queue import priority_for


@dataclass(frozen=True, slots=True)
class RecordedObservation:
    observation: Observation
    decision: DiagnosticDecision


def diagnostics_enabled() -> bool:
    explicit = os.getenv("DIAGNOSTIC_QUEUE_ENABLED")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.getenv("SITE_INVESTIGATOR_COMMAND", "").strip())


class ObservationService:
    def __init__(
        self,
        store: SQLiteEventStore,
        *,
        run_id: str,
        jsonl_export: Path | None = None,
    ) -> None:
        self.store = store
        self.run_id = run_id
        self.jsonl_export = jsonl_export

    def record(
        self,
        *,
        provider_id: str,
        url: str,
        observed_at: str,
        transport: str,
        state: str,
        duration_ms: int,
        http_status: int | None,
        page_hash: str,
        html_changed: bool,
        classifier_reason: str,
        error_category: str | None,
        diagnostic_events: Iterable[str],
        mode: str,
        discovery_stage: str = "LANDING",
        evidence: Iterable[str] = (),
        request_trace: Iterable[RequestTraceEntry] = (),
    ) -> RecordedObservation:
        observation = Observation(
            observation_id=make_observation_id(provider_id),
            run_id=self.run_id,
            provider_id=provider_id,
            observed_at=observed_at,
            transport=transport,
            state=state,
            duration_ms=duration_ms,
            http_status=http_status,
            page_hash=page_hash,
            html_changed=html_changed,
            classifier_reason=classifier_reason,
            error_category=error_category,
            discovery_stage=discovery_stage,
            evidence=tuple(evidence),
            request_trace=tuple(request_trace),
        )

        events = sorted(
            set(diagnostic_events),
            key=lambda event: (priority_for(event), event),
        )
        request: DiagnosticSnapshotRequest | None = None
        if not events:
            outcome = "NOT_REQUIRED"
            reason_code = "NO_DIAGNOSTIC_EVENT"
            event = None
            investigation_id = None
        elif not diagnostics_enabled():
            outcome = "DISABLED"
            reason_code = "DIAGNOSTICS_DISABLED"
            event = events[0]
            investigation_id = None
        else:
            outcome = "ACCEPTED"
            reason_code = "DIAGNOSTIC_POLICY_MATCHED"
            event = events[0]
            investigation_id = make_investigation_id()
            request = DiagnosticSnapshotRequest(
                investigation_id=investigation_id,
                observation_id=observation.observation_id,
                run_id=self.run_id,
                provider_id=provider_id,
                url=url,
                event=event,
                reason=classifier_reason,
                mode=mode,
                page_hash=page_hash,
                requested_at=utc_now(),
            )

        decision = DiagnosticDecision(
            decision_id=make_decision_id(),
            observation_id=observation.observation_id,
            decided_at=utc_now(),
            outcome=outcome,
            reason_code=reason_code,
            event=event,
            investigation_id=investigation_id,
        )
        self.store.record(observation, decision, request)
        self._append_export(observation)
        return RecordedObservation(observation, decision)

    def _append_export(self, observation: Observation) -> None:
        """Write a disposable analysis-friendly mirror; SQLite remains truth."""
        if self.jsonl_export is None:
            return
        self.jsonl_export.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_export.open("a", encoding="utf-8") as stream:
            json.dump(
                observation.to_dict(),
                stream,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            stream.write("\n")
