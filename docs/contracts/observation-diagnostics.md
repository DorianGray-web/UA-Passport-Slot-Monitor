# Observation and Diagnostic Processing Contract

## Architectural invariant

`Observation` is the immutable source-of-truth domain event for one provider
check: at a specific time, the monitor observed exactly this result. It is
never updated with later diagnostic, notification, or analytics state.

Every persisted contract has an explicit `schema_version`. Observation v2 is
current; diagnostic contracts remain v1.

## Causal model

```text
Observation
    |
    v
DiagnosticDecision
    |
    v
DiagnosticJob
    |
    v
InvestigationResult
```

Notifications and analytics are independent reactions linked to the same
`observation_id`.

## Observation v2

Required fields:

- `schema_version`;
- `observation_id`;
- `run_id`;
- `provider_id`;
- `observed_at`;
- `transport`;
- `state`;
- `duration_ms`;
- `http_status`;
- `page_hash`;
- `html_changed`;
- `classifier_reason`;
- `error_category`;
- `discovery_stage`;
- typed `evidence`;
- sanitized `request_trace`.

`discovery_stage` is one of `LANDING`, `SERVICE_VALIDATION`, `DAYS`, or
`TIMES`. Trace items contain method, logical operation, status, duration,
response size, attempt, and transport. They never contain CSRF, headers,
request bodies, cookies, tokens, fingerprints, or personal data.

`request_count` is computed as `len(request_trace)` and is not persisted.

Fields such as `notification_sent`, `diagnostics_requested`, queue status, and
worker status are forbidden because they are not facts observed by the
monitor.

SQLite is the source-of-truth store. Per-provider JSON Lines files are
disposable, analysis-friendly mirrors of Observation records.

## Transactional decision and outbox

The monitor-side application service stores the following in one SQLite
transaction:

1. the Observation;
2. exactly one DiagnosticDecision;
3. an outbox record only when the decision is `ACCEPTED`.

An accepted decision therefore survives dispatcher, queue, or process failure.
The dispatcher retries pending outbox records without blocking a monitor.

## Infrastructure boundaries

`DiagnosticDispatcher` depends only on:

```text
DispatchTarget.dispatch(snapshot)
```

`DiagnosticWorker` depends only on:

```text
DiagnosticQueue.claim()
DiagnosticQueue.complete()
DiagnosticQueue.fail()
DiagnosticBackend.investigate()
```

The queue knows only immutable `DiagnosticSnapshotRequest` payloads and safe
`InvestigationResult` values. It must not know about Playwright, Chromium, HAR,
video, screenshots, npm, or Site Investigator.

## Queue behavior

The initial SQLite queue and test-only memory queue implement the same
contracts. Queue jobs support:

- priority ordering;
- configurable-policy cooldown defaults;
- active-job deduplication by provider, mode, event, and page hash;
- bounded worker leases;
- lease tokens that reject completion by stale workers;
- reclamation of jobs whose leases expired;
- retry and terminal failure states.

Default priority order:

1. `SLOTS_AVAILABLE`;
2. `CAPTCHA_REQUIRED` and `BLOCKED`;
3. `UNKNOWN`;
4. `HTML_STRUCTURE_CHANGED` and `QUEUE_SECTION_CHANGED`.

Every priority and cooldown can be overridden without changing monitors:

```text
DIAGNOSTIC_PRIORITY_<EVENT>
DIAGNOSTIC_COOLDOWN_<EVENT>
```

Cooldown values are seconds. Defaults are zero for `SLOTS_AVAILABLE`, five
minutes for CAPTCHA or blocking, fifteen minutes for `UNKNOWN`, and thirty
minutes for structural changes.

## Runtime correlation

The orchestrator creates one `run_id` and passes it to every provider process
and the diagnostic worker. A provider restart inside the same orchestrator
session retains that `run_id`. Every check receives a unique
`observation_id`; every accepted diagnostic decision receives a stable
`investigation_id`.

## Operational records

Dispatcher retries and infrastructure errors belong to operational logs, not
the domain model. Logs may be rotated or removed without losing Observation,
Decision, Job, or Result history.
