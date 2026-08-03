"""Immutable logical decisions and reproducible decision traces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    parse_utc_timestamp,
    require_observation_ids,
    require_positive,
    require_sha256,
    require_text,
)


__architecture_layer__ = "decision"


class NotificationDecisionStage(str, Enum):
    CONFIRMATION = "CONFIRMATION"
    DEDUPLICATION = "DEDUPLICATION"
    PRIORITY = "PRIORITY"
    PRIVACY = "PRIVACY"
    ROUTING = "ROUTING"


class NotificationDecisionOutcome(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    SUPPRESSED = "SUPPRESSED"


@dataclass(frozen=True)
class NotificationDecision:
    decision_id: str
    decision_trace_id: str
    sequence_number: int
    candidate_id: str
    event_id: str | None
    stage: NotificationDecisionStage
    outcome: NotificationDecisionOutcome
    reason_code: str
    policy_set_id: str
    policy_set_version: int
    policy_id: str
    policy_version: int
    policy_hash: str
    source_observation_ids: tuple[str, ...]
    decided_at: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in (
            "decision_id", "decision_trace_id", "candidate_id", "reason_code",
            "policy_set_id", "policy_id",
        ):
            require_text(getattr(self, name), name)
        require_positive(self.sequence_number, "sequence_number")
        require_positive(self.policy_set_version, "policy_set_version")
        require_positive(self.policy_version, "policy_version")
        require_sha256(self.policy_hash, "policy_hash")
        require_observation_ids(self.source_observation_ids)
        parse_utc_timestamp(self.decided_at, "decided_at")
        if self.schema_version != 1:
            raise ValueError("unsupported NotificationDecision schema_version")


@dataclass(frozen=True)
class DecisionTrace:
    decision_trace_id: str
    candidate_id: str
    policy_set_id: str
    decisions: tuple[NotificationDecision, ...]

    def __post_init__(self) -> None:
        require_text(self.decision_trace_id, "decision_trace_id")
        require_text(self.candidate_id, "candidate_id")
        require_text(self.policy_set_id, "policy_set_id")
        if not self.decisions:
            raise ValueError("DecisionTrace requires at least one decision")
        for expected, decision in enumerate(self.decisions, start=1):
            if decision.sequence_number != expected:
                raise ValueError("decision sequence numbers must be contiguous")
            if decision.decision_trace_id != self.decision_trace_id:
                raise ValueError("decision_trace_id mismatch")
            if decision.candidate_id != self.candidate_id:
                raise ValueError("candidate_id mismatch")
            if decision.policy_set_id != self.policy_set_id:
                raise ValueError("policy_set_id mismatch")
