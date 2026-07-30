"""Immutable diagnostic domain contracts.

Observation is the source-of-truth domain event. Decisions, jobs, and results
are separate records linked by stable identifiers.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 1
OBSERVATION_SCHEMA_VERSION = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return (
        f"{prefix}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-"
        f"{uuid.uuid4().hex[:8]}"
    )


@dataclass(frozen=True, slots=True)
class RequestTraceEntry:
    method: str
    operation: str
    status_code: int | None
    duration_ms: int
    response_bytes: int
    attempt: int = 1
    transport: str = "http"


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    run_id: str
    provider_id: str
    observed_at: str
    transport: str
    state: str
    duration_ms: int
    http_status: int | None
    page_hash: str
    html_changed: bool
    classifier_reason: str
    error_category: str | None = None
    discovery_stage: str = "LANDING"
    evidence: tuple[str, ...] = ()
    request_trace: tuple[RequestTraceEntry, ...] = ()
    schema_version: int = OBSERVATION_SCHEMA_VERSION

    @property
    def request_count(self) -> int:
        return len(self.request_trace)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshotRequest:
    investigation_id: str
    observation_id: str
    run_id: str
    provider_id: str
    url: str
    event: str
    reason: str
    mode: str
    page_hash: str
    requested_at: str
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiagnosticDecision:
    decision_id: str
    observation_id: str
    decided_at: str
    outcome: str
    reason_code: str
    event: str | None
    investigation_id: str | None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DispatchReceipt:
    accepted: bool
    investigation_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ClaimedJob:
    investigation_id: str
    request: DiagnosticSnapshotRequest
    priority: int
    attempt: int
    lease_token: str
    lease_until: str


@dataclass(frozen=True, slots=True)
class QueueJobError:
    category: str
    message: str
    retryable: bool = True


def make_observation_id(provider_id: str) -> str:
    slug = provider_id.rsplit("-", 1)[-1].upper()
    return new_id(f"OBS-{slug}")


def make_run_id() -> str:
    return new_id("RUN")


def make_decision_id() -> str:
    return new_id("DEC")


def make_investigation_id() -> str:
    return new_id("INV")
