"""Offline notification domain governed by ADR-0012.

This package has no runtime, provider, worker, adapter, or delivery integration.
"""

from .contracts import (
    ConfirmedNotificationEvent,
    NotificationAudience,
    NotificationCandidate,
    NotificationDeliveryJob,
    NotificationEnvelope,
    NotificationEventType,
    NotificationPriority,
    NotificationProvenance,
    PublicNotificationFacts,
)
from .decisions import (
    DecisionTrace,
    NotificationDecision,
    NotificationDecisionOutcome,
    NotificationDecisionStage,
)
from .policy_loader import (
    NotificationPolicyConfiguration,
    PolicyConfigurationError,
    load_policy_configuration,
)
from .replay import normalized_replay_result, replay
from .queue import (
    ClaimedDeliveryJob,
    DeliveryJobStatus,
    NotificationDeliveryState,
    SQLiteDeliveryJobStore,
)

__all__ = [
    "ConfirmedNotificationEvent",
    "ClaimedDeliveryJob",
    "DecisionTrace",
    "DeliveryJobStatus",
    "NotificationCandidate",
    "NotificationAudience",
    "NotificationDeliveryJob",
    "NotificationEnvelope",
    "NotificationDecision",
    "NotificationDecisionOutcome",
    "NotificationDecisionStage",
    "NotificationEventType",
    "NotificationPriority",
    "NotificationPolicyConfiguration",
    "NotificationDeliveryState",
    "NotificationProvenance",
    "PolicyConfigurationError",
    "PublicNotificationFacts",
    "SQLiteDeliveryJobStore",
    "load_policy_configuration",
    "normalized_replay_result",
    "replay",
]
