"""Offline notification domain governed by ADR-0012.

This package has no runtime, provider, scheduler, network, or external delivery integration.
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
from .worker import (
    DeliveryResult,
    DeliveryStatus,
    DeliveryWorkerOutcome,
    DeliveryWorkerRun,
    LocalDeliveryAdapter,
    NotificationDeliveryWorker,
)

__all__ = [
    "ConfirmedNotificationEvent",
    "ClaimedDeliveryJob",
    "DecisionTrace",
    "DeliveryResult",
    "DeliveryStatus",
    "DeliveryWorkerOutcome",
    "DeliveryWorkerRun",
    "DeliveryJobStatus",
    "NotificationCandidate",
    "NotificationAudience",
    "NotificationDeliveryJob",
    "NotificationEnvelope",
    "NotificationDecision",
    "NotificationDecisionOutcome",
    "NotificationDecisionStage",
    "NotificationEventType",
    "NotificationDeliveryWorker",
    "NotificationPriority",
    "NotificationPolicyConfiguration",
    "NotificationDeliveryState",
    "NotificationProvenance",
    "LocalDeliveryAdapter",
    "PolicyConfigurationError",
    "PublicNotificationFacts",
    "SQLiteDeliveryJobStore",
    "load_policy_configuration",
    "normalized_replay_result",
    "replay",
]
