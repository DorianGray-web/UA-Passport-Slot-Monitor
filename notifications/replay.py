"""Pure offline confirmation replay; never schedules provider observations."""

from __future__ import annotations

import hashlib
import json

from .contracts import NotificationCandidate, parse_utc_timestamp, require_text
from .decisions import (
    DecisionTrace,
    NotificationDecision,
    NotificationDecisionOutcome,
    NotificationDecisionStage,
)
from .policy_loader import NotificationPolicyConfiguration, PolicyConfigurationError


__architecture_layer__ = "decision"


def _hash_policy(policy: object) -> str:
    normalized = json.dumps(dict(policy), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def replay(
    candidate: NotificationCandidate,
    configuration: NotificationPolicyConfiguration,
    policy_set_id: str,
    retained_state: tuple[NotificationDecision, ...] = (),
    *,
    decision_id: str,
    decision_trace_id: str,
    evaluation_time: str,
) -> DecisionTrace:
    """Reproduce a confirmation trace from explicit inputs without mutation."""

    require_text(decision_id, "decision_id")
    require_text(decision_trace_id, "decision_trace_id")
    evaluated = parse_utc_timestamp(evaluation_time, "evaluation_time")
    policy_set = configuration.policy_set(policy_set_id)
    sequence_number = len(retained_state) + 1
    if not configuration.enabled or not policy_set.enabled:
        outcome = NotificationDecisionOutcome.REJECTED
        reason = "POLICY_SET_DISABLED"
    else:
        reference = policy_set.reference("confirmation")
        policy = configuration.policy("confirmation", reference)
        first = parse_utc_timestamp(candidate.first_observed_at, "first_observed_at")
        last = parse_utc_timestamp(candidate.last_observed_at, "last_observed_at")
        count = len(candidate.source_observation_ids)
        duration = int((last - first).total_seconds())
        age = int((evaluated - first).total_seconds())
        required_states = tuple(policy["required_states"])
        required_stage = policy["required_stage"]
        facts = candidate.public_facts
        if age < 0:
            raise PolicyConfigurationError("evaluation_time precedes candidate observations")
        if age > policy["maximum_window_seconds"]:
            outcome = NotificationDecisionOutcome.EXPIRED
            reason = "CONFIRMATION_WINDOW_EXPIRED"
        elif facts.discovery_stage != required_stage or facts.state not in required_states:
            outcome = NotificationDecisionOutcome.REJECTED
            reason = "REQUIRED_FACTS_NOT_MATCHED"
        elif count < policy["minimum_observations"] or duration < policy["minimum_duration_seconds"]:
            outcome = NotificationDecisionOutcome.PENDING
            reason = "CONFIRMATION_INCOMPLETE"
        else:
            outcome = NotificationDecisionOutcome.ACCEPTED
            reason = "CONFIRMATION_SATISFIED"

    reference = policy_set.reference("confirmation")
    policy = configuration.policy("confirmation", reference)
    decision = NotificationDecision(
        decision_id=decision_id,
        decision_trace_id=decision_trace_id,
        sequence_number=sequence_number,
        candidate_id=candidate.candidate_id,
        event_id=None,
        stage=NotificationDecisionStage.CONFIRMATION,
        outcome=outcome,
        reason_code=reason,
        policy_set_id=policy_set.policy_set_id,
        policy_set_version=policy_set.policy_set_version,
        policy_id=reference.policy_id,
        policy_version=reference.policy_version,
        policy_hash=_hash_policy(policy),
        source_observation_ids=candidate.source_observation_ids,
        decided_at=evaluation_time,
    )
    return DecisionTrace(
        decision_trace_id=decision_trace_id,
        candidate_id=candidate.candidate_id,
        policy_set_id=policy_set.policy_set_id,
        decisions=(*retained_state, decision),
    )


def normalized_replay_result(trace: DecisionTrace) -> tuple[tuple[str, str, str, str, int, str, int], ...]:
    """Return the ID- and timestamp-independent logical replay result."""

    return tuple(
        (
            decision.stage.value,
            decision.outcome.value,
            decision.reason_code,
            decision.policy_set_id,
            decision.policy_set_version,
            decision.policy_id,
            decision.policy_version,
        )
        for decision in trace.decisions
    )
