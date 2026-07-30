# Kortrijk Monitor v1 — Implementation Plan

## Status

Partially implemented; live verification and notification slices remain open.

## Source specification

`specs/2026-07-26-kortrijk-queue-observation.md`

## Objective

Implement the first passive Kortrijk queue observer that:

- uses HTTP-first observation;
- requests operationally separate browser diagnostics when required;
- classifies normalized queue states;
- records minimal metadata;
- detects state transitions;
- stores sanitized diagnostics only when required;
- sends selected notifications.

## Constraints

- no booking actions;
- no CAPTCHA solving;
- no personal data;
- no cookies or reusable session data in Git;
- no browser profile committed;
- no raw authorization headers;
- no production auto-booking logic.

## Existing implementation to review

- `providers/dp-document/kortrijk_monitor.py`
- `research/dp-document/tools/kortrijk_browser_spike.py`
- existing research documents;
- existing runtime ignore rules;
- existing notification documentation.

## Implementation slices

### Slice 1 — Domain model and normalized states

Create or refine:

- queue-state enum;
- observation result model;
- transition model;
- classifier reason;
- error category.

Covers:

- `AC-5`
- `AC-7`
- `AC-8`
- `AC-14`
- `AC-15`

### Slice 2 — HTTP observer

Implement:

- direct GET request;
- timeout;
- response-time measurement;
- HTTP status recording;
- HTML hashing;
- classifier invocation;
- blocked/challenge detection.

Covers:

- `AC-2`
- `AC-5`
- `AC-15`

### Slice 3 — State classifier

Implement confirmed markers for:

- `NO_SLOTS`;
- `SLOTS_AVAILABLE`;
- `CAPTCHA_REQUIRED`;
- `BLOCKED`;
- `UNKNOWN`;
- `ERROR`.

Classifier output must include:

- normalized state;
- matched marker or reason;
- confidence/evidence note where useful.

Covers:

- `AC-5`
- `AC-13`
- `AC-14`
- `AC-15`

### Slice 4 — Separate diagnostics

Normal monitoring remains HTTP-only. On blocked, challenged, or insufficient
evidence it records an unresolved state and may enqueue a diagnostic snapshot.
Playwright belongs only to the separately supervised diagnostic backend.

Covers:

- `AC-3`
- `AC-4`

### Slice 5 — Observation persistence

Store one minimal record per completed cycle:

- UTC timestamp;
- method;
- response time;
- normalized state;
- HTTP status;
- HTML hash;
- classifier reason;
- error category.

Recommended format for v1:

- JSON Lines or SQLite.

JSON Lines was selected for the initial monitoring metadata implementation.

Covers:

- `AC-5`
- `AC-6`

### Slice 6 — Transition detection

Implement:

- loading previous recorded state;
- initial-state handling;
- transition creation;
- distinction between repeated state and changed state.

Covers:

- `AC-7`
- `AC-8`

### Slice 7 — Diagnostic snapshots

On relevant transition, save sanitized:

- HTML;
- screenshot;
- extracted text;
- network summary;
- transition metadata.

Do not save repeated full snapshots for unchanged states.

Covers:

- `AC-6`
- `AC-9`
- `AC-10`
- `AC-13`

### Slice 8 — Notifications

Implement immediate notification for:

- `SLOTS_AVAILABLE`;
- `CAPTCHA_REQUIRED`;
- `UNKNOWN`.

Notification payload:

- provider;
- location;
- timestamp;
- previous/current state;
- method;
- reason;
- local diagnostic reference.

Decision required:

- Telegram first;
- email fallback;
- local console only for initial test.

Covers:

- `AC-11`
- `AC-12`
- `AC-13`

### Slice 9 — Scheduling and backoff

Implement:

- randomized regular interval of 7–12 minutes;
- separate bounded retry/backoff policy;
- prevention of tight retry loops;
- optional escalation after repeated `BLOCKED` or `ERROR`.

Covers:

- `AC-1`
- implementation detail for failure handling.

## Proposed file changes

Possible files:

```text
providers/dp-document/kortrijk_monitor.py
research/dp-document/tools/kortrijk_browser_spike.py
providers/dp-document/kortrijk_states.py
providers/dp-document/kortrijk_classifier.py
providers/dp-document/kortrijk_storage.py
providers/dp-document/kortrijk_notifications.py
tests/providers/dp-document/test_kortrijk_classifier.py
tests/providers/dp-document/test_kortrijk_transitions.py
tests/providers/dp-document/test_kortrijk_storage.py
tests/fixtures/dp-document/kortrijk/
```

Exact structure may be simplified after reviewing the existing code.

## Test strategy

### Unit tests

Test:

- state-marker matching;
- blocked-response detection;
- unknown-state behavior;
- HTML hash generation;
- initial-state behavior;
- state-transition detection;
- unchanged-state behavior;
- notification trigger rules;
- sensitive-header sanitization;
- randomized interval boundaries.

### Fixture-based tests

Create sanitized fixtures for:

- no slots;
- slots available;
- CAPTCHA;
- Cloudflare/403;
- unknown page;
- malformed or empty response.

### Integration tests

Test locally:

- HTTP success without Playwright;
- HTTP failure followed by an unresolved state and optional diagnostic request;
- repeated NO_SLOTS;
- transition NO_SLOTS -> SLOTS_AVAILABLE;
- transition into UNKNOWN;
- diagnostic failure without interruption of monitoring.

## Manual verification

Verify:

- no form submission;
- no navigation into booking flow;
- no cookies/tokens in logs;
- no runtime artifacts tracked by Git;
- screenshots created only under defined conditions;
- notification includes no sensitive data.

## Acceptance-criteria traceability

Acceptance criterion      Implementation slice     Verification
AC-1                      Slice 9                  interval boundary tests
AC-2                      Slice 2                  HTTP-only integration test
AC-3                      Slice 4                  fallback integration test
AC-4                      Slice 4                  code review and manual verification
AC-5                      Slices 1, 2, 5           persistence tests
AC-6                      Slices 5, 7              sanitization tests
AC-7                      Slice 6                  transition tests
AC-8                      Slice 6                  initial-state test
AC-9                      Slice 7                  transition snapshot test
AC-10                     Slice 7                  repeated-state test
AC-11                     Slice 8                  notification test
AC-12                     Slice 8                  CAPTCHA notification test
AC-13                     Slices 3, 7, 8           unknown-state integration test
AC-14                     Slices 1, 3              error classification test
AC-15                     Slices 2, 3              blocked-response tests

## Implementation order

- review existing code;
- freeze state model;
- write classifier fixtures and tests;
- implement HTTP observer;
- implement transition persistence;
- add separate diagnostic requests;
- add diagnostic snapshots;
- add notifications;
- add scheduler and backoff;
- run verification against all AC-N.

## Open implementation decisions

Before coding, resolve:

- Telegram or console-first notification;
- snapshot retention period;
- exact blocked/error retry thresholds;
- whether ERROR participates in business-state transitions;
- diagnostic browser profile policy outside MonitorProvider;
- exact sanitization fields for network summaries.

## Definition of done

The implementation is complete when:

- every AC-1–AC-15 has verification evidence;
- all automated tests pass;
- no sensitive runtime artifacts are tracked;
- HTTP-first behavior is confirmed;
- any browser diagnostics remain operationally separate;
- notification behavior is demonstrated;
- a verification report exists under reports/verification/.
