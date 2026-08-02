# Notification Event Contracts

> **Status:** Proposed; no runtime implementation

This document defines the planned immutable contracts for the evidence-first
Output Pipeline in
[ADR-0012](../DECISIONS.md#adr-0012-evidence-first-notification-derivation-and-output-isolation).
It does not change Observation v3 or the implemented diagnostic contracts.

## Causal model

```text
Observation
    -> NotificationCandidate
    -> NotificationDecision[] / Decision Trace
    -> ConfirmedNotificationEvent
    -> NotificationDeliveryJob
    -> DeliveryResult
    -> NotificationAuditRecord[]
```

Notification state is never written into Observation.

## Common rules

Every persisted contract:

- is immutable;
- has an explicit `schema_version`;
- uses UTC ISO-8601 timestamps;
- uses stable prefixed identifiers;
- contains only allowlisted sanitized fields;
- rejects unsupported versions and unknown required semantics;
- remains independent from channel credentials and provider runtime objects.

Suggested identifier prefixes:

```text
NCAND  Notification Candidate
NDEC   Notification Decision
NTRACE Decision Trace correlation
NEVT   Confirmed Notification Event
NJOB   Notification Delivery Job
NAUD   Notification Audit Record
```

## Enums

### Event types

Minimum proposed categories:

| Category | Event types |
|---|---|
| Critical | `SLOTS_AVAILABLE`, `QUEUE_FORM_FOUND`, `RUNTIME_CONTRACT_DEVIATION` |
| Warning | `REPEATED_BLOCKED`, `SCHEMA_DEVIATION`, `RUNTIME_GUARD_REFUSAL` |
| Information | `RUN_COMPLETED`, `RESEARCH_SUMMARY_GENERATED`, `GOVERNANCE_REMINDER`, `PROFILE_VALIDATION_FINISHED` |
| Debug | `DEVELOPER_DIAGNOSTIC` |

Information and governance events require an approved Operational Fact source
and must not be fabricated as provider Observations.

### Priority

`P0`, `P1`, `P2`, and `P3` represent urgency. Priority does not imply an
audience or delivery channel.

### Audience

Initial values are `developer`, `research`, and future `public`.

### Decision stage and outcome

Stages:

```text
CONFIRMATION
DEDUPLICATION
PRIORITY
PRIVACY
ROUTING
```

Outcomes:

```text
PENDING
ACCEPTED
REJECTED
EXPIRED
SUPPRESSED
```

## PublicNotificationFacts v1

Allowlisted normalized fields:

```text
provider_display_name: string | null
service_display_name: string | null
state: string | null
discovery_stage: string | null
observed_at: string
available_dates_count: integer | null
available_time_slots_count: integer | null
earliest_available_time: string | null
latest_available_time: string | null
official_url: string | null
reason_code: string | null
```

Raw Observation serialization is forbidden. Builders construct this contract
field by field.

## NotificationCandidate v1

```text
candidate_id: string
event_type: NotificationEventType
provider_id: string | null
run_id: string | null
source_observation_ids: non-empty array[string]
first_observed_at: string
last_observed_at: string
public_facts: PublicNotificationFacts v1
schema_version: 1
```

A Candidate represents a potentially communicable fact. It does not authorize
delivery.

## NotificationDecision v1

```text
decision_id: string
decision_trace_id: string
sequence_number: positive integer
candidate_id: string
event_id: string | null
stage: NotificationDecisionStage
outcome: NotificationDecisionOutcome
reason_code: string
policy_set_id: string
policy_set_version: positive integer
policy_id: string
policy_version: positive integer
policy_hash: lowercase SHA-256
source_observation_ids: non-empty array[string]
decided_at: string
schema_version: 1
```

Within one Decision Trace, `sequence_number` is unique and strictly ordered.
Decisions are append-only. A completed trace cannot be edited to make a later
delivery appear successful.

## NotificationProvenance v1

```text
source_observation_ids: non-empty array[string]
candidate_id: string
decision_trace_id: string
policy_set_id: string
policy_set_version: positive integer
policy_set_hash: lowercase SHA-256
confirmation_policy_id: string
confirmation_policy_version: positive integer
confirmation_count: positive integer
first_observed_at: string
last_observed_at: string
evaluation_time: string
confirmation_window_seconds: non-negative integer
deduplication_policy_id: string
deduplication_policy_version: positive integer
priority_policy_id: string
priority_policy_version: positive integer
privacy_policy_id: string
privacy_policy_version: positive integer
routing_policy_id: string
routing_policy_version: positive integer
schema_version: 1
```

Hashes cover normalized safe policy content only. Credentials and resolved
destination identifiers are excluded.

## ConfirmedNotificationEvent v1

```text
event_id: string
event_type: NotificationEventType
provider_id: string | null
run_id: string | null
confirmed_at: string
public_facts: PublicNotificationFacts v1
provenance: NotificationProvenance v1
schema_version: 1
```

A Confirmed Event exists only after an accepted confirmation decision. It is
still subject to deduplication, privacy, and routing decisions before delivery.

## NotificationEnvelope v1

```text
event_id: string
priority: NotificationPriority
audience: NotificationAudience
title: string
body: string
official_url: string | null
occurred_at: string
schema_version: 1
```

This is the only event-facing payload a Delivery Adapter receives. It cannot
contain Observation, provider monitor, policy engine, or governance objects.

## NotificationDeliveryJob v1

```text
job_id: string
event_id: string
decision_trace_id: string
priority: NotificationPriority
audience: NotificationAudience
channel: string
destination_alias: string
envelope: NotificationEnvelope v1
dedup_key: string
queued_at: string
available_at: string
schema_version: 1
```

The immutable job contains a destination alias, never a bot token or resolved
recipient ID. Lease token, lease expiry, retry count, and queue status are
infrastructure columns rather than fields in the immutable request payload.

## DeliveryResult v1

```text
success: boolean
channel: string
provider_message_id: string | null
error_category: string | null
retryable: boolean
completed_at: string
schema_version: 1
```

`provider_message_id` is optional and sanitized. Raw channel response bodies,
recipient IDs, request headers, and exception text are forbidden.

## NotificationAuditRecord v1

```text
audit_id: string
candidate_id: string | null
event_id: string | null
job_id: string | null
decision_trace_id: string | null
action: NotificationAuditAction
reason_code: string
policy_set_id: string | null
policy_version: integer | null
channel: string | null
destination_alias: string | null
occurred_at: string
schema_version: 1
```

Minimum actions:

```text
CANDIDATE_CREATED
CONFIRMATION_PENDING
CANDIDATE_CONFIRMED
CANDIDATE_EXPIRED
CANDIDATE_DISCARDED
EVENT_DEDUPLICATED
EVENT_AGGREGATED
DELIVERY_QUEUED
DELIVERY_CLAIMED
DELIVERY_SUCCEEDED
DELIVERY_RETRY_SCHEDULED
DELIVERY_FAILED
PRIVACY_REJECTED
CONFIGURATION_REJECTED
```

Audit explains operational handling. It does not replace NotificationDecision
and cannot change its logical outcome.

## Decision Trace integrity

A trace is reconstructible by sorting immutable NotificationDecision records
by `sequence_number` for one `decision_trace_id`.

Integrity checks require:

- exactly one Candidate and Policy Set per trace;
- unique, contiguous sequence numbers;
- policy references on every decision;
- accepted mandatory stages before a Delivery Job exists;
- no Delivery Job after a rejected privacy or routing decision;
- all source Observation IDs in provenance to be present in the Candidate.

## Privacy rules

The following are forbidden in every notification contract, queue payload,
audit record, log, and outbound envelope:

```text
cookies
CSRF values
request or response headers
authorization values
request bodies
raw provider responses
raw HTML
browser storage or browser-profile paths
HAR, trace, screenshot, or video data
phone numbers, OTP, CAPTCHA, or identity data
booking payloads
bot tokens or resolved recipient identifiers
arbitrary exception or channel response bodies
```

## Versioning rules

Each contract evolves independently. A supported system may therefore consume
Candidate v1, Decision v2, Confirmed Event v1, and Delivery Job v1 if an
explicit compatibility rule allows that combination.

A schema version changes when:

- a required field is added, removed, or changes type;
- the meaning of an existing field changes;
- allowed values change incompatibly;
- an old consumer cannot safely interpret the payload.

A schema version does not change for:

- confirmation counts or windows;
- deduplication cooldowns;
- priority mappings;
- routing destinations;
- Policy Set enablement;
- provider-specific notification overrides;
- message wording.

Those changes update policy IDs, policy versions, policy hashes, or Policy Set
versions. Consumers accept only explicitly supported schema versions and fail
closed on unsupported semantics.

## Reproducibility contract

Logical replay input consists of retained source Observations, deterministic
ordering, referenced policies, evaluation time, and relevant retained
confirmation and deduplication state. Normalized replay output consists of
Decision stages, outcomes, reason codes, priority, routes, provenance, and
policy references.

New IDs, replay execution timestamps, external channel responses, and audit
actions are excluded from semantic equality.

