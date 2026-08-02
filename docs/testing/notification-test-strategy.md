# Notification Test Strategy

> **Status:** Proposed; documentation milestone only

This document defines the validation strategy for the planned evidence-first
Output Pipeline. It accompanies
[ADR-0012](../DECISIONS.md#adr-0012-evidence-first-notification-derivation-and-output-isolation)
and the [notification contracts](../contracts/notification-events.md).

No notification implementation or external delivery is introduced here.

## Test levels

```text
Contract Tests
    -> Policy Tests
    -> Decision Replay Tests
    -> Integration Tests
```

## Contract Tests

Contract tests validate each immutable model independently:

- required fields and supported enums;
- frozen/immutable behavior;
- deterministic safe serialization;
- independent schema versions;
- identifier and timestamp formats;
- references between Candidate, Decision, Event, Job, Result, and Audit;
- Decision Trace sequence integrity;
- rejection of unsupported schemas and unknown required semantics;
- absence of forbidden fields and arbitrary nested data.

The configuration schema is checked using valid and invalid fixtures. Invalid
Policy Sets, unresolved policy references, credentials embedded in JSON, raw
destination IDs, and unexpected properties must fail closed.

## Policy Tests

Each policy is tested without Coordinator, queue, worker, or adapter:

### Confirmation

- one observation remains pending when more are required;
- matching natural observations satisfy count and duration requirements;
- maximum-window expiry produces `EXPIRED`;
- reset states reject a pending Candidate;
- consecutive requirements are enforced;
- required discovery stages are enforced;
- provider overrides apply only when explicitly declared;
- policy evaluation never calls or schedules provider runtime.

### Deduplication

- equivalent confirmed events inside a silence window are suppressed;
- aggregation retains source Observation provenance;
- different providers and event subjects do not collide;
- recovery may create a new event when explicitly configured;
- retained state produces the same decision after restart.

### Priority

- event-to-priority mappings are explicit;
- unknown event types fail closed;
- priority never selects audience or channel.

### Privacy

- only allowlisted public fields pass;
- unknown fields fail closed;
- nested cookies, CSRF, headers, storage, HTML, captures, identity, tokens,
  destinations, and exception bodies are rejected;
- validation is safe both before queue insertion and before delivery.

### Routing

- audience and channel are selected independently from priority;
- disabled routes produce no jobs;
- destination aliases remain unresolved in domain events;
- missing destinations become sanitized configuration failures;
- routing does not import or inspect provider runtime.

## Decision Replay Tests

Replay validates reproducibility:

```text
Retained source Observations
+ deterministic ordering
+ referenced Policy Set
+ evaluation time
+ retained confirmation/deduplication state
    -> replay
    -> same normalized Decision Trace
```

Semantic comparison includes:

- decision stages and ordering;
- outcomes and reason codes;
- policy IDs, versions, and safe hashes;
- confirmation counts and intervals;
- priority and routing results;
- source Observation provenance;
- normalized public facts.

Semantic comparison excludes:

- newly generated IDs;
- test execution timestamps;
- worker lease data;
- external channel responses;
- operational audit actions.

Representative replay fixtures cover:

- transient `SLOTS_AVAILABLE -> NO_SLOTS` rejection;
- confirmed consecutive availability;
- availability counts changing while availability remains true;
- repeated `BLOCKED` aggregation;
- schema deviation confirmation and reset;
- duplicate suppression across Coordinator restart;
- unsupported policy and schema refusal.

## Integration Tests

The initial integration harness uses synthetic or retained sanitized
Observations, a test Observation reader, MemoryNotificationQueue, and a fake
adapter. It makes no external network calls.

```text
Observation reader
    -> Coordinator
    -> policies and Decision Trace
    -> Memory/SQLite Notification Queue
    -> worker
    -> fake adapter
    -> Delivery Result and Audit
```

Integration cases include:

- disabled notifications produce zero jobs and external calls;
- Coordinator restart resumes from the durable cursor;
- candidate replay does not duplicate a visible delivery;
- queue leases recover an interrupted worker;
- stale lease tokens cannot complete a job;
- retryable and terminal failures remain distinct;
- adapter failure cannot affect monitoring or source Observations;
- Privacy Policy rejection prevents queue insertion or delivery;
- accepted routing plus failed delivery remains logically consistent;
- channel adapters receive only Notification Envelopes.

## Architecture Tests

Static dependency tests enforce output isolation:

- provider monitors do not import notification modules;
- notification policies do not import provider monitors;
- Coordinator does not import Telegram or other concrete adapters;
- Telegram adapter does not import Observation;
- adapters cannot read `providers.json` or the Evidence Matrix;
- notification modules cannot write trusted provider configuration;
- no policy component can schedule an HTTP or Playwright check;
- notification settings are absent from `providers.json`.

## Privacy regression vocabulary

Fixtures and serialized values are scanned case-insensitively for forbidden
categories, including:

```text
cookie
set-cookie
csrf
authorization
bearer
token
phone
otp
captcha
storage
html
har
trace
fingerprint
passport number
```

Tests use synthetic values only and never real credentials, destination IDs,
cookies, or provider session material.

## Live validation order

Live Telegram delivery is outside the first implementation milestone. If a
developer-only adapter is later approved, validation order is:

```text
contract and policy tests
    -> replay tests
    -> architecture tests
    -> fake adapter integration
    -> SQLite queue restart validation
    -> developer-only bounded delivery
    -> governance review
    -> optional runtime integration
```

Public recipients require a later privacy and governance review. Developer
validation cannot automatically enable public notification capability.

## Release traceability criterion

When any externally deliverable profile is enabled, release validation must
show that every Delivery Job is reproducible from retained source facts,
retained logical decision state, the referenced versioned Policy Set, and the
recorded evaluation context.

When no profile is enabled, notification traceability is recorded as not
applicable rather than treated as implemented.

