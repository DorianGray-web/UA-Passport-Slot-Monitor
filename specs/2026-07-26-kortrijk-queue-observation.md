# Kortrijk Queue Observation

## Status

Approved; partially implemented. This specification remains the requirement
baseline, not a statement that every acceptance criterion is complete. See the
implementation plan and verification reports for current evidence.

## Goal

Passively observe the Kortrijk electronic queue state without modifying,
advancing, or otherwise affecting the booking process.

## Rationale

The project needs reliable evidence about queue availability and state
transitions before implementing user-facing monitoring.

The observer should minimize:

- requests to the provider;
- browser automation;
- retained runtime data;
- privacy and security risks.

## Scope

This specification covers passive observation of:

- the public queue page;
- the state visible during a completed observation;
- transitions between consecutive observations;
- HTTP-first observation;
- separate diagnostics when HTTP observation is insufficient;
- local metadata recording;
- notifications for selected states.

## Non-goals

The observer must not perform:

- booking;
- automatic slot reservation;
- CAPTCHA solving or bypassing;
- account creation;
- identity verification;
- payment;
- form submission;
- navigation beyond what is required to determine the observable queue state;
- exporting, publishing, or committing cookies, authorization data, browser
  profiles, or personal data;

## Queue states

The observer recognizes the following normalized states:

- `NO_SLOTS`
- `SLOTS_AVAILABLE`
- `CAPTCHA_REQUIRED`
- `BLOCKED`
- `UNKNOWN`
- `ERROR`

### State definitions

#### NO_SLOTS

The provider page was successfully observed and contains confirmed markers
indicating that no appointment slots are currently available.

#### SLOTS_AVAILABLE

The provider page was successfully observed and contains confirmed markers
indicating that one or more appointment slots may be available.

#### CAPTCHA_REQUIRED

The observer encountered a CAPTCHA or an equivalent user-verification step
that prevents passive state determination.

#### BLOCKED

The provider or an intermediary rejected or challenged the observation,
including access denial, rate limiting, or a Cloudflare challenge.

#### UNKNOWN

The observation completed, but the available evidence did not match any
confirmed state classifier.

#### ERROR

The observation could not be completed because of a local runtime,
network, parsing, browser, or persistence failure.

## Observation interval

Successful observation cycles must use a randomized delay of:

- minimum: 7 minutes;
- maximum: 12 minutes.

The delay must be selected independently for each new cycle.

Retries caused by transient failures may use a separate bounded backoff policy,
defined in the implementation plan.

## Observation strategy

### Preferred method

Use direct HTTP observation when the response provides enough evidence to
classify the queue state.

### HTTP queue discovery

Normal monitoring uses the confirmed pre-authentication DP Document flow:

```text
Service -> form=days -> form=times
```

Days requires `ServiceCenterId`, `ServiceId`, and CSRF. Times additionally
requires `Date`. Fingerprint generation and Playwright are not dependencies.

Blocked, challenged, or insufficient HTTP evidence must produce `BLOCKED`,
`UNKNOWN`, or `ERROR`. It may enqueue separate diagnostics, but the monitor
must not launch browser automation.

## Normal observation record

For every completed observation cycle, store:

- timestamp in UTC;
- observation method;
- response time;
- normalized state;
- HTTP status code when available;
- HTML content hash when HTML is available;
- classifier reason or matched marker;
- error category when applicable.

Do not store:

- cookies;
- authorization headers;
- session tokens;
- browser profile data;
- personal data;
- complete request headers unless explicitly sanitized.

## State transitions

A state transition occurs when the current normalized state differs from the
previous successfully recorded normalized state.

Example:

```text
NO_SLOTS -> SLOTS_AVAILABLE

```

The first recorded observation establishes the initial state and is not treated
as a transition.

## Diagnostic snapshot policy

When a state transition is detected, save a sanitized diagnostic snapshot
containing, when available:

- HTML;
- screenshot;
- extracted visible text;
- sanitized network summary;
- previous state;
- current state;
- transition timestamp;
- observation method.

Snapshots must not contain:

- cookies;
- authorization headers;
- session tokens;
- personal identifiers;
- reusable browser-profile data.

A repeated observation with the same state must not create another full
diagnostic snapshot unless explicitly required for error investigation.

The implementation may distinguish between:

- `minimal` capture for normal observations;
- `diagnostic` capture for state transitions and controlled investigations.

## Notification policy

Send an immediate notification when a completed observation results in:

- SLOTS_AVAILABLE;
- CAPTCHA_REQUIRED;
- UNKNOWN.

A notification should include:

- timestamp;
- provider and location;
- current state;
- previous state when available;
- observation method;
- short classifier reason;
- local diagnostic reference when available.

Notifications must not include raw cookies, tokens, authorization data, or
personal data.

Notification behavior for BLOCKED and ERROR is defined by the
implementation plan and may use aggregation or thresholds to avoid excessive
alerts.

## Acceptance criteria

### AC-1

When an observation cycle completes successfully,
the system shall schedule the next regular observation after a randomized
delay between 7 and 12 minutes inclusive.

### AC-2

When the queue state can be classified from the HTTP response,
the system shall classify and record the state without launching a browser.

### AC-3

When HTTP observation fails, is blocked, is challenged, or provides
insufficient classification evidence, the system shall record a safe
unresolved state and may request operationally separate diagnostics without
launching Playwright inside the monitor.

### AC-4

While performing HTTP observation or separate diagnostics,
the system shall not submit booking forms, reserve slots, solve CAPTCHA,
create accounts, perform payments, or enter personal data.

### AC-5

When an observation cycle completes,
the system shall record the timestamp, observation method, response time,
normalized state, and available HTML hash.

### AC-6

When observation metadata or diagnostic artifacts are persisted,
the system shall exclude cookies, authorization credentials, session tokens,
browser-profile data, and personal data.

### AC-7

When the current normalized state differs from the previous recorded
normalized state,
the system shall record a transition containing the previous state,
current state, and timestamp.

### AC-8

When no previous observation exists,
the system shall store the current state as the initial state without
classifying it as a transition.

### AC-9

When a state transition is detected,
the system shall save the available sanitized HTML, screenshot, extracted
text, and network summary.

### AC-10

While consecutive completed observations produce the same normalized state,
the system shall not create repeated full diagnostic snapshots for that state.

### AC-11

When the normalized state becomes SLOTS_AVAILABLE,
the system shall send an immediate notification.

### AC-12

When the normalized state becomes CAPTCHA_REQUIRED,
the system shall send an immediate notification without attempting to solve
or bypass the CAPTCHA.

### AC-13

When a completed observation is classified as UNKNOWN,
the system shall save diagnostic evidence and send an immediate notification.

### AC-14

When an observation cannot be completed because of a local or network
failure,
the system shall record ERROR together with a non-sensitive error category.

### AC-15

When the provider rejects, rate-limits, or challenges an observation,
the system shall classify the result as BLOCKED rather than
NO_SLOTS.

## Success criteria

The observer:

- reliably classifies every completed observation into one normalized state;
- records every detected transition between consecutive observations;
- distinguishes absence of slots from blocked, unknown, and failed observations;
- minimizes browser use and unnecessary diagnostic storage;
- does not affect the booking process;
- does not retain sensitive or personal data.

## Open questions

The implementation plan must resolve:

- confirmed markers for each state;
- hash normalization rules;
- retry and backoff behavior;
- notification transport;
- notification deduplication;
- snapshot retention period;
- sanitization rules for the network summary;
- whether transitions involving ERROR count as business-state transitions.

### Browser identity and network constraints

Normal monitoring must not create or use a browser identity. Any browser used
by separate diagnostics remains outside MonitorProvider.

The observer must not:

- spoof or randomize the browser fingerprint;
- patch browser APIs to disguise automation;
- rotate proxies or IP addresses;
- distribute requests across multiple hosts;
- run concurrent browser identities against the same provider;
- automatically solve or continue through an anti-bot challenge.

Separate diagnostic or research tooling may manage its own browser profile
under its own privacy controls. MonitorProvider must not create, retain, or
depend on that profile.
