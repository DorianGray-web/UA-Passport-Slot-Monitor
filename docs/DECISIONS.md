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

**Status:** Superseded in part by ADR-0010 for explicitly enabled, confirmed
research profiles. Fingerprinting and booking exclusions remain accepted.

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

DP Document monitoring is HTTP-first and follows the public
`Service -> days -> times` flow. The HTTP MonitorProvider remains independent
from browser fingerprinting and booking behavior.

Fingerprint generation is not a monitoring dependency and must not be
implemented, invoked, emulated, spoofed, persisted, or transmitted by a
MonitorProvider.

Playwright is not the default transport. It may be used only by operationally
separate diagnostics, controlled reverse engineering, or the explicitly
enabled experimental transport defined by ADR-0010.

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

## ADR-0009: Transition from City Entry Points to a Registry-driven Generic DP Document Monitor

**Status:** Accepted; implementation deferred

**Date:** 2026-07-31

### Context

The first DP Document centres were implemented as separate executable
entrypoints such as `berlin_monitor.py`, `bratislava_monitor.py`, and
`kortrijk_monitor.py`.

That structure was intentional during early provider research:

- each centre could be started, stopped, and diagnosed independently;
- a centre-specific experiment could be isolated from the other monitors;
- configuration and logging boundaries remained obvious;
- adding Berlin and Bratislava did not require an early abstraction over an
  unstable protocol;
- failures in one entrypoint did not prevent the orchestrator from supervising
  the others.

The current nine-centre research sample still uses independent processes and
entrypoints. City-specific values have moved into
`providers/dp-document/providers.json`, but each process continues to start
through a city-named script. This implementation is working and covered by
offline tests.

The number of expected DP Document centres may grow to 18 or more. At that
scale, maintaining a nearly identical entrypoint file for every city would add
repetitive files without adding isolation beyond the process boundary already
provided by the orchestrator.

### Decision

Keep the existing city entrypoints for the current live-research stage.

After the DP Document monitoring protocol and deployment configuration have
stabilized, replace the duplicated city scripts with one generic executable,
conceptually:

```text
monitor_runner
    |
    +-- DPDocumentMonitor --city berlin
    +-- DPDocumentMonitor --city bratislava
    +-- DPDocumentMonitor --city madrid
    +-- ...
```

Each invocation will remain an independent operating-system process. The
generic monitor will resolve its city exclusively through the provider
registry and will continue to produce city-specific logs, state, and metadata.

The transition must not merge provider processes or move protocol behavior
into the registry. `LandingPageClassifier`, `DiscoveryEngine`,
`TransitionGuard`, Observation, and the diagnostic subsystem remain shared
runtime contracts rather than configuration.

### Transition criteria

The refactor may begin when all of the following are true:

1. the multi-centre research observation stage is complete;
2. landing, days, and times protocol stages have stable classifiers and
   transition rules;
3. required deployment-specific configuration fields are known;
4. the registry can represent all supported centre differences without
   executable city-specific logic;
5. regression tests can prove equivalent process supervision, logging,
   metadata, environment overrides, and manual-stop behavior;
6. the expected provider set or maintenance cost justifies removing the
   wrappers, with expansion toward 18 or more centres being the current
   planning signal.

If a centre requires genuine protocol behavior that cannot be represented by
configuration, it must use an explicit adapter or strategy boundary. The
generic monitor must not accumulate city-name conditionals.

### Consequences

- the tested city-entrypoint implementation remains unchanged during live
  research;
- the registry is the migration boundary for future centre expansion;
- adding centres before the transition may still require a small wrapper;
- after the transition, adding a normal DP Document centre should require only
  a registry entry;
- process isolation, per-city logs, per-city JSONL mirrors, and shared
  `run_id` correlation remain intact;
- the future refactor has explicit readiness criteria instead of being
  triggered only by file count;
- a one-off centre difference will be modeled as an adapter capability, not as
  branching inside a universal monitor.

## ADR-0010: Experimental Playwright Discovery Transport Fallback

**Status:** Experimental; opt-in research only

**Date:** 2026-07-31

### Context

Runtime evidence shows that direct HTTP access may alternate between confirmed
public responses and HTTP `403` protection pages. Passive browser observations
confirm that an ordinary browser session can expose the public
`LANDING -> DAYS -> TIMES` workflow for Madrid, Barcelona, London, and Milan
without identity verification or booking.

### Decision

Introduce an opt-in `PlaywrightDiscoveryTransport` for Madrid, Barcelona,
London, and Milan only. Every cycle remains HTTP-first:

```text
HTTP confirmed discovery -> Observation(transport=http)
HTTP BLOCKED             -> Playwright persistent context
Playwright TIMES         -> Observation(transport=playwright) -> STOP
```

The feature is disabled by default and requires
`PLAYWRIGHT_DISCOVERY_FALLBACK_ENABLED=true`. The browser uses one persistent
local profile per provider under Git-ignored `.browser-data/`. It performs one
navigation, changes only confirmed public service/date selectors, and reads
`days`/`times` through the same strict classifiers as HTTP.

It must not interact with CAPTCHA, identity fields, continuation controls, or
booking. It must not use fingerprint spoofing, stealth plugins, proxies, IP
rotation, challenge bypass, artificial retries, screenshots, HAR, or payload
persistence. A challenge remains `BLOCKED`; unexpected DOM or JSON becomes
`UNKNOWN`.

Observation schema v3 remains unchanged. A successful fallback records
`transport=playwright`; its sanitized trace retains the initial HTTP attempt
and subsequent browser stages.

### Consequences

- HTTP remains the preferred low-overhead transport;
- browser execution is limited to four evidence-confirmed profiles;
- persistent state remains local and excluded from source control;
- existing polling intervals bound browser frequency to one attempt per
  blocked cycle;
- Site Investigator remains a separate optional diagnostic subsystem;
- adoption outside these profiles requires separate evidence and validation.

### Subsequent validation

On 2026-07-31, a bounded 3h57m run across the four confirmed profiles recorded
79 browser fallbacks after HTTP `403`. All 79 reached `TIMES` and produced
`SLOTS_AVAILABLE`; no browser errors, unexpected browser `UNKNOWN`, CAPTCHA
interactions, identity-data interactions, or booking actions were recorded.
This validates the experimental transport for those four profiles only. It
does not establish equivalent behavior for other centres or prove that the
public `days`/`times` protocol is fundamentally inaccessible over HTTP.
