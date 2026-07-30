# Multi-provider Monitoring and Orchestration Plan

## Status

Implemented and offline-validated, including asynchronous diagnostic queue
infrastructure. Authorized live verification is pending.

## Objective

Extend the passive DP Document research monitor from Kortrijk to Berlin and
Bratislava while keeping every provider independently executable and adding a
small process supervisor for combined operation.

## Implemented scope

- independent Kortrijk, Berlin, and Bratislava monitor entrypoints;
- provider-specific URL, identifier, environment-variable namespace, state
  file, metadata stream, and log file;
- HTTP-only normal observation with separate browser diagnostics;
- randomized 7–12 minute polling and bounded failure backoff;
- optional external diagnostic requests without importing investigator
  internals;
- one append-only JSON Lines metadata stream per provider;
- concurrent process startup, lifecycle logging, restart, and coordinated
  shutdown through `monitor_runner.py`;
- Git exclusion for logs, metadata, state, captures, and browser profiles.
- immutable schema-versioned Observation and DiagnosticDecision records;
- atomic Observation, Decision, and outbox persistence;
- backend-agnostic dispatcher and queue interfaces;
- separate diagnostic worker supervised by the orchestrator;
- SQLite priority, cooldown, deduplication, lease-token, retry, and
  expired-lease recovery behavior.
- evidence-first landing classification with guarded transitions;
- Observation schema v2 with DiscoveryStage, Evidence, and RequestTrace.

## Runtime outputs

```text
logs/
    kortrijk.log
    berlin.log
    bratislava.log
    orchestrator.log
    diagnostic-worker.log

metadata/
    kortrijk.jsonl
    berlin.jsonl
    bratislava.jsonl

data/
    observations.sqlite3
    diagnostic-queue.sqlite3
```

Each metadata record contains:

- UTC timestamp;
- provider identifier;
- normalized state;
- HTTP transport for normal observations;
- diagnostic decision and correlation data are authoritative in SQLite;
- whether the normalized HTML hash changed;
- response time in milliseconds;
- HTTP status, when available.

## Verification completed

- all monitor and runner modules compile;
- standardized metadata records are covered by offline tests;
- different HTML produces `html_changed=true` after an initial observation;
- Berlin and Bratislava expose distinct provider identifiers and URLs;
- the existing Kortrijk diagnostic regression suite remains passing;
- the repository's offline `unittest` suite passed at the time of the latest
  verification; the current count is intentionally not frozen in this plan;
- `git diff --check` passes.

No live request to Berlin or Bratislava was part of this verification.

## Live verification remaining

- confirm provider-specific no-slots markers;
- observe HTTP 200, blocked, throttled, and challenge responses;
- verify HTTP days/times discovery and separate diagnostic recovery;
- confirm centre-specific HTTP session and CSRF behavior without bypassing
  access controls;
- confirm that metadata remains append-only during long-running operation;
- exercise orchestrator restart and Ctrl+C shutdown during a monitored session.

## Analysis follow-up

Add a read-only analysis tool that combines the three JSONL streams and reports:

- HTML changes grouped by local hour and UTC hour;
- changes occurring across multiple centres within a configurable time window;
- update clusters after midnight and during morning hours;
- delay from an HTML hash change to `SLOTS_AVAILABLE`;
- country and centre-level differences in frequency, latency, and transport.

The analysis must treat `BLOCKED`, `CAPTCHA_REQUIRED`, `UNKNOWN`, and `ERROR`
as unresolved observations, never as evidence of no availability.
