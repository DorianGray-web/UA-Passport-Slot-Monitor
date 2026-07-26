# Kortrijk Monitor v1 — Implementation Plan

## Status

Draft

## Source specification

`specs/2026-07-26-kortrijk-queue-observation.md`

## Objective

Implement the first passive Kortrijk queue observer that:

- uses HTTP-first observation;
- falls back to Playwright when required;
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
- `providers/dp-document/kortrijk_browser_spike.py`
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

### Slice 4 — Playwright fallback

Implement passive browser fallback only when:

- HTTP request fails;
- response is blocked;
- response is challenged;
- response is insufficient for classification.

The browser flow must not:

- submit forms;
- enter personal data;
- solve CAPTCHA;
- continue into booking.

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

Decision required before implementation.

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
providers/dp-document/kortrijk_browser_spike.py
providers/dp-document/kortrijk_states.py
providers/dp-document/kortrijk_classifier.py
providers/dp-document/kortrijk_storage.py
providers/dp-document/kortrijk_notifications.py
tests/providers/dp-document/test_kortrijk_classifier.py
tests/providers/dp-document/test_kortrijk_transitions.py
tests/providers/dp-document/test_kortrijk_storage.py
tests/fixtures/dp-document/kortrijk/
