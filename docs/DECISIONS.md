# Architecture Decision Records (ADR)

This document records significant architectural and product decisions made during the development of UA Passport Slot Monitor.

Each decision captures the context, reasoning, and expected consequences to help future contributors understand why specific approaches were chosen.

---

## ADR-0001 — Privacy-first Architecture

**Status:** Accepted

**Date:** 2026-07-19

### Context

UA Passport Slot Monitor is intended to help users monitor appointment availability for Ukrainian document services without becoming another system that unnecessarily collects personal information.

Many modern online services collect more information than is required for their primary function. Since this project is being designed from the ground up, privacy principles can be integrated into the architecture from the very beginning.

### Decision

The project adopts a **Privacy-first** architecture.

Every new feature must first answer the following question:

> Can this feature work without collecting personal data?

If the answer is yes, the feature should be implemented without collecting personal information.

If personal data is genuinely required, the project should collect only the minimum amount necessary for the intended function.

### Consequences

This decision affects the entire architecture of the project.

Examples include:

- avoiding unnecessary storage of personal information;
- preferring local processing whenever possible;
- requiring explicit user consent for optional features;
- making location services optional;
- avoiding automatic CAPTCHA solving;
- avoiding automatic appointment confirmation;
- documenting all new data categories before implementation.

### Rationale

The decision supports:

- user trust;
- GDPR principles;
- privacy by design;
- easier security review;
- simpler compliance in future releases;
- responsible open-source development.

This decision is expected to remain one of the core principles of the project.

---

## ADR-0002 — Browser-assisted Provider Adapters

**Status:** Accepted generally; DP Document monitoring is governed by ADR-0007

**Date:** 2026-07-21

### Context

Some public appointment applications reject standard HTTP clients even though the same application is available through a normal browser session. Provider behavior may also depend on client-side JavaScript and session state.

### Decision

A provider adapter may use a real browser session when standard HTTP access cannot reliably observe the public appointment workflow.

Browser use is limited to accessing the same public workflow available to a normal user. It must not be used to bypass CAPTCHA, Cloudflare challenges, rate limits, authentication, or other access controls.

When a challenge is detected, the adapter must stop or pause and return a distinct status that may trigger manual user intervention.

### Consequences

- Browser-session management becomes part of the provider layer.
- Provider checks are more resource-intensive than simple HTTP requests.
- Session lifecycle, backoff, and safe concurrency require explicit design.
- Challenge detection is a required feature, not an exceptional workaround.

---

## ADR-0003 — Validate Evidence Before Interpreting Availability

**Status:** Accepted

**Date:** 2026-07-21

### Context

A provider check can return a target application response, a protection page, a CAPTCHA, an error, an incomplete capture, or an unexpected application state. Treating every response without visible slots as `NO_SLOTS` would create false results.

### Decision

Provider data may be interpreted only after the captured response has been validated as belonging to the intended appointment application and containing a recognized, complete state.

Protection pages, incomplete captures, unresolved application states, and parsing failures must return `BLOCKED`, `UNKNOWN`, or `ERROR` as appropriate. They must never return `NO_SLOTS`.

### Consequences

- Capture validation is a separate architectural stage.
- Provider adapters require explicit positive evidence for `NO_SLOTS`.
- Unknown provider changes fail safely instead of silently misleading users.
- Monitoring reliability can be measured independently from slot availability.

---

## ADR-0004 — Separate Monitoring from Appointment Booking

**Status:** Accepted

**Date:** 2026-07-21

### Context

Availability monitoring can help users notice short-lived openings without requiring the project to collect the personal and document information needed to complete an appointment registration.

### Decision

The project monitors and reports availability changes only. Final appointment selection, CAPTCHA completion, submission, and confirmation remain manual user actions on the official provider website.

### Consequences

- The system does not automatically reserve or book appointments.
- Passport numbers and document details are outside the monitoring scope.
- Notifications must direct users to the official provider flow.
- The architecture remains simpler and more privacy-preserving.

## ADR-0005: Passive browser fallback for protected provider pages

**Status:** Superseded by ADR-0007 for DP Document runtime monitoring

**Date:** 2026-07-28

### Context

The Kortrijk queue page is publicly accessible through a normal browser.

During provider research and a continuous 24-hour observation run, direct HTTP
requests were frequently rejected or challenged by the provider-side
protection layer. Direct HTTP access occasionally succeeded, but was not
reliable enough to serve as the only observation method.

The project requires a reliable way to determine only the publicly visible
queue state without entering or automating the booking process.

### Decision

Provider adapters should prefer direct HTTP observation when it returns enough
evidence for reliable classification.

A provider may use a passive Playwright fallback when:

- direct HTTP access fails;
- the response is rejected or challenged;
- the response does not contain enough evidence;
- the required public state is available only after browser rendering.

The browser fallback must preserve the behaviour of one ordinary local browser
session.

It must not use:

- proxy or IP rotation;
- distributed request sources;
- browser fingerprint spoofing;
- stealth plugins intended to conceal automation;
- automated CAPTCHA solving;
- challenge bypass;
- account or identity automation;
- automatic booking or form submission.

If the browser session is challenged, the observer must report `BLOCKED`,
apply bounded backoff, and wait for a later observation.

### Consequences

Positive:

- the provider can be observed reliably when direct HTTP access is
  intermittently blocked;
- HTTP remains available as the lowest-overhead path;
- the monitor does not require identity-disguising or challenge-bypass
  mechanisms;
- the approach remains compatible with manual completion of CAPTCHA and booking.

Negative:

- Playwright consumes more local resources than direct HTTP;
- persistent browser profiles may contain sensitive session artifacts;
- browser behaviour and provider-side protection rules may change;
- `BLOCKED` must be treated as an expected observation condition, not as proof
  of queue availability.

### Security and privacy constraints

Browser profiles, cookies, tokens, local storage, screenshots, network captures,
and diagnostic artifacts must not be committed to Git or included in public
release archives.

Any external diagnostic tool must remain optional, local, and operationally
separate from the public monitor.

## ADR-0006: Separate runtime monitoring from local diagnostic tooling

**Status:** Accepted

**Date:** 2026-07-28

### Context

The public monitor requires minimal state classification, while controlled
research may require richer HTML, screenshot, DOM, and network diagnostics.

### Decision

The public monitor and local diagnostic tooling remain operationally separate.

```text
Public monitor
        |
        +-- runtime observation
        |
        +-- optional local diagnostics
```

The monitor must continue operating without the diagnostic tool. Diagnostic
capture must remain optional, local, sanitized, and outside version control.

### Consequences

- normal monitoring retains less data;
- diagnostic collection can evolve independently;

## ADR-0007: Exclude browser fingerprinting and automation from DP Document monitoring

**Status:** Accepted

**Date:** 2026-07-30

### Context

Reverse-engineering of DP Document frontend version 7.34.2 confirmed two
independent workflows. Public, pre-authentication queue discovery uses:

```text
Service -> form=days -> form=times
```

The requests require `ServiceCenterId`, `ServiceId`, a CSRF token, and `Date`
for times. They do not require a browser fingerprint.

Fingerprint generation is initialized by the booking frontend and appended
only by `submitFormClassic`, `submitFormCombo`, `submitFormBankID`, and
`submitFormDiia`. Module 708 contains an embedded ThumbmarkJS implementation
that collects browser characteristics and hashes them locally. No ThumbmarkJS
API request was observed during queue discovery.

### Decision

DP Document monitoring is HTTP-only and follows the public
`Service -> days -> times` flow.

Fingerprint generation is not a monitoring dependency and must not be
implemented, invoked, emulated, spoofed, persisted, or transmitted by a
MonitorProvider.

Playwright is excluded from normal queue discovery. Browser automation may be
used only by operationally separate diagnostics, controlled reverse
engineering, or separately approved future booking research.

Monitoring and any future booking implementation use independent boundaries:

```text
MonitorProvider              BookingProvider
get_days()                   separately approved scope
get_times()                  no current implementation
```

No booking provider or fingerprint implementation is introduced by this
decision.

### Consequences

- normal monitoring no longer launches Chromium or maintains a browser
  profile;
- HTTP requests remain suitable for constrained hosts;
- CAPTCHA, HTTP protection, or unexpected responses produce `BLOCKED`,
  `UNKNOWN`, or `ERROR` and may enqueue separate diagnostics;
- Site Investigator remains outside the provider runtime;
- future booking research cannot add fingerprint dependencies to
  MonitorProvider.

## ADR-0008: Evidence-first provider protocol

**Status:** Accepted

**Date:** 2026-07-30

### Context

DP Document can terminate discovery at different protocol stages. When no
dates are available, landing HTML can contain the confirmed
`Наразі всі місця зайняті` marker and no AJAX follows. When a queue form is
available, the frontend proceeds through days and times.

Landing HTML is therefore provider evidence, not merely an application shell.

### Decision

Monitoring uses an evidence-first guarded state machine:

```text
LANDING
  | confirmed terminal evidence -> stop
  | valid form and CSRF          -> SERVICE_VALIDATION
                                       |
                                       v
                                     DAYS
                                       |
                                       v
                                     TIMES
```

`LandingPageClassifier` is independent from MonitorProvider and returns a
typed `LandingPageResult` containing state, extracted CSRF, optional queue
form, and Evidence codes. Every transition requires positive evidence.

Observation persists DiscoveryStage, accumulated Evidence, and a sanitized
RequestTrace. Request count is derived from trace length.

### Consequences

- confirmed no-slots HTML requires only one GET;
- AJAX runs only when transition guards allow it;
- blocked or unfamiliar HTML cannot become `NO_SLOTS`;
- traces support latency, response-size, retry, and request-load analysis;
- days/times transitions remain disabled until explicit response classifiers
  exist.
