# Pre-identity Calendar Observation Extension

## Status

**Partially implemented.** The public `DAYS -> TIMES -> STOP` contract and
Observation schema v3 are implemented for nine governed profiles. Kortrijk
and Chisinau remain landing-only, and the rendered identity-boundary
classifier and fixture remain open.

> **Supersession note — 2026-08-02:** The six-hour release validation completed
> bounded runtime coverage for the four profiles promoted on 2026-08-02.

## Scope

Extend monitoring only across publicly observable DP Document discovery:

```text
LANDING -> SERVICE_VALIDATION -> DAYS -> TIMES -> STOP
```

The monitor must stop before identity verification. Booking, fingerprinting,
OTP, BankID, Diia, identity data, and reservation submission are excluded.

## Proposed observable states

Availability state and discovery stage remain separate concepts.

Normalized states:

- `NO_SLOTS`
- `POSSIBLE_SLOTS`
- `SLOTS_AVAILABLE`
- `CAPTCHA_REQUIRED`
- `BLOCKED`
- `UNKNOWN`
- `ERROR`

Discovery stages:

- `LANDING`
- `SERVICE_VALIDATION`
- `DAYS`
- `TIMES`
- monitoring terminates at `TIMES`.

## Confirmed public-discovery evidence codes

- `AVAILABLE_DATES_FOUND`
- `AVAILABLE_TIMES_FOUND`
- `NO_AVAILABLE_DATES`
- `NO_AVAILABLE_TIMES`
- `DAYS_PAYLOAD_UNRECOGNIZED`
- `TIMES_PAYLOAD_UNRECOGNIZED`

## Immutable Observation extension

Schema version 3 records:

```text
available_dates_count: int | null
available_time_slots_count: int | null
earliest_available_time: local time | null
latest_available_time: local time | null
```

Rules:

- fields describe public availability only;
- no selected applicant, phone, identity, OTP, session, cookie, CSRF, request
  body, or fingerprint data may be stored;
- counts remain `null` when a stage or payload is unconfirmed; absence is not
  zero;
- time-slot count means allowed public time entries, not inferred appointment
  capacity;
- raw HTML and payloads remain local research evidence, not Observation data;
- the Observation remains immutable;
- `TIMES` is terminal for the monitor.

## Acceptance evidence required

- confirmed Madrid landing evidence with service and CSRF-field semantics;
- confirmed non-empty Madrid days and times response schemas;
- negative synthetic fixtures for malformed days and times payloads;
- negative fixtures for challenge, error, login, and unexpected payloads;
- proof that no test or runtime path submits booking or identity data.
