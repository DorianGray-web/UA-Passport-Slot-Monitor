"""Immutable contracts for the offline notification domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from datetime import datetime, timezone
import re


__architecture_layer__ = "candidate"


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def require_positive(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def parse_utc_timestamp(value: str, field_name: str) -> datetime:
    require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field_name} must use UTC")
    return parsed


def require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def require_observation_ids(values: tuple[str, ...]) -> None:
    if not isinstance(values, tuple) or not values:
        raise ValueError("source_observation_ids must be a non-empty tuple")
    for value in values:
        require_text(value, "source_observation_ids item")
    if len(set(values)) != len(values):
        raise ValueError("source_observation_ids must be unique")


class NotificationEventType(str, Enum):
    SLOTS_AVAILABLE = "SLOTS_AVAILABLE"
    QUEUE_FORM_FOUND = "QUEUE_FORM_FOUND"
    RUNTIME_CONTRACT_DEVIATION = "RUNTIME_CONTRACT_DEVIATION"
    REPEATED_BLOCKED = "REPEATED_BLOCKED"
    SCHEMA_DEVIATION = "SCHEMA_DEVIATION"
    RUNTIME_GUARD_REFUSAL = "RUNTIME_GUARD_REFUSAL"
    RUN_COMPLETED = "RUN_COMPLETED"
    RESEARCH_SUMMARY_GENERATED = "RESEARCH_SUMMARY_GENERATED"
    GOVERNANCE_REMINDER = "GOVERNANCE_REMINDER"
    PROFILE_VALIDATION_FINISHED = "PROFILE_VALIDATION_FINISHED"
    DEVELOPER_DIAGNOSTIC = "DEVELOPER_DIAGNOSTIC"


class NotificationPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class NotificationAudience(str, Enum):
    DEVELOPER = "developer"
    RESEARCH = "research"
    PUBLIC = "public"


@dataclass(frozen=True)
class PublicNotificationFacts:
    observed_at: str
    provider_display_name: str | None = None
    service_display_name: str | None = None
    state: str | None = None
    discovery_stage: str | None = None
    available_dates_count: int | None = None
    available_time_slots_count: int | None = None
    earliest_available_time: str | None = None
    latest_available_time: str | None = None
    official_url: str | None = None
    reason_code: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        parse_utc_timestamp(self.observed_at, "observed_at")
        if self.schema_version != 1:
            raise ValueError("unsupported PublicNotificationFacts schema_version")
        for name in ("available_dates_count", "available_time_slots_count"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"{name} must be a non-negative integer or null")


@dataclass(frozen=True)
class NotificationCandidate:
    candidate_id: str
    event_type: NotificationEventType
    provider_id: str | None
    run_id: str | None
    source_observation_ids: tuple[str, ...]
    first_observed_at: str
    last_observed_at: str
    public_facts: PublicNotificationFacts
    schema_version: int = 1

    def __post_init__(self) -> None:
        require_text(self.candidate_id, "candidate_id")
        require_observation_ids(self.source_observation_ids)
        first = parse_utc_timestamp(self.first_observed_at, "first_observed_at")
        last = parse_utc_timestamp(self.last_observed_at, "last_observed_at")
        if first > last:
            raise ValueError("first_observed_at must not be after last_observed_at")
        if self.schema_version != 1:
            raise ValueError("unsupported NotificationCandidate schema_version")


@dataclass(frozen=True)
class NotificationProvenance:
    source_observation_ids: tuple[str, ...]
    candidate_id: str
    decision_trace_id: str
    policy_set_id: str
    policy_set_version: int
    policy_set_hash: str
    confirmation_policy_id: str
    confirmation_policy_version: int
    confirmation_count: int
    first_observed_at: str
    last_observed_at: str
    evaluation_time: str
    confirmation_window_seconds: int
    deduplication_policy_id: str
    deduplication_policy_version: int
    priority_policy_id: str
    priority_policy_version: int
    privacy_policy_id: str
    privacy_policy_version: int
    routing_policy_id: str
    routing_policy_version: int
    schema_version: int = 1

    def __post_init__(self) -> None:
        require_observation_ids(self.source_observation_ids)
        for name in (
            "candidate_id", "decision_trace_id", "policy_set_id", "confirmation_policy_id",
            "deduplication_policy_id", "priority_policy_id", "privacy_policy_id",
            "routing_policy_id",
        ):
            require_text(getattr(self, name), name)
        for name in (
            "policy_set_version", "confirmation_policy_version", "confirmation_count",
            "deduplication_policy_version", "priority_policy_version",
            "privacy_policy_version", "routing_policy_version",
        ):
            require_positive(getattr(self, name), name)
        require_sha256(self.policy_set_hash, "policy_set_hash")
        first = parse_utc_timestamp(self.first_observed_at, "first_observed_at")
        last = parse_utc_timestamp(self.last_observed_at, "last_observed_at")
        parse_utc_timestamp(self.evaluation_time, "evaluation_time")
        if first > last:
            raise ValueError("first_observed_at must not be after last_observed_at")
        if self.confirmation_window_seconds < 0:
            raise ValueError("confirmation_window_seconds must be non-negative")
        if self.schema_version != 1:
            raise ValueError("unsupported NotificationProvenance schema_version")


@dataclass(frozen=True)
class ConfirmedNotificationEvent:
    event_id: str
    event_type: NotificationEventType
    provider_id: str | None
    run_id: str | None
    confirmed_at: str
    public_facts: PublicNotificationFacts
    provenance: NotificationProvenance
    schema_version: int = 1

    def __post_init__(self) -> None:
        require_text(self.event_id, "event_id")
        parse_utc_timestamp(self.confirmed_at, "confirmed_at")
        if self.schema_version != 1:
            raise ValueError("unsupported ConfirmedNotificationEvent schema_version")


@dataclass(frozen=True)
class NotificationEnvelope:
    event_id: str
    priority: NotificationPriority
    audience: NotificationAudience
    title: str
    body: str
    official_url: str | None
    occurred_at: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in ("event_id", "title", "body"):
            require_text(getattr(self, name), name)
        parse_utc_timestamp(self.occurred_at, "occurred_at")
        if self.official_url is not None:
            require_text(self.official_url, "official_url")
        if self.schema_version != 1:
            raise ValueError("unsupported NotificationEnvelope schema_version")


@dataclass(frozen=True)
class NotificationDeliveryJob:
    job_id: str
    event_id: str
    decision_trace_id: str
    priority: NotificationPriority
    audience: NotificationAudience
    channel: str
    destination_alias: str
    envelope: NotificationEnvelope
    dedup_key: str
    queued_at: str
    available_at: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in (
            "job_id", "event_id", "decision_trace_id", "channel",
            "destination_alias", "dedup_key",
        ):
            require_text(getattr(self, name), name)
        queued = parse_utc_timestamp(self.queued_at, "queued_at")
        available = parse_utc_timestamp(self.available_at, "available_at")
        if available < queued:
            raise ValueError("available_at must not be before queued_at")
        if self.envelope.event_id != self.event_id:
            raise ValueError("envelope event_id must match job event_id")
        if self.envelope.priority != self.priority:
            raise ValueError("envelope priority must match job priority")
        if self.envelope.audience != self.audience:
            raise ValueError("envelope audience must match job audience")
        if self.schema_version != 1:
            raise ValueError("unsupported NotificationDeliveryJob schema_version")
