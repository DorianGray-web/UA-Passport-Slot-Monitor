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

The current twelve-centre research sample still uses independent processes and
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
`LANDING -> DAYS -> TIMES` workflow for Madrid, Barcelona, London, Milan, and Valencia
without identity verification or booking.

### Decision

Introduce an opt-in `PlaywrightDiscoveryTransport` only for explicitly
governed, evidence-confirmed registry profiles. The initial scope was Madrid,
Barcelona, London, Milan, and Valencia. Every cycle remains HTTP-first:

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
- browser execution is limited to registry-enabled, evidence-confirmed
  profiles admitted through ADR-0011 governance;
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

On 2026-08-01, owner-provided passive browser evidence confirmed Valencia
centre `7`, service `4`, the public days/times request sequence, and compatible
response schemas. Valencia was therefore admitted as a fifth evidence-gated
profile. Its transport reliability remains subject to a separate bounded
runtime validation.

Also on 2026-08-01, owner-provided passive browser evidence confirmed Berlin
centre `2`, service `4`, and the same bounded public sequence. Berlin reached
`DAYS` with one allowed date (`2026-08-31`) and then `TIMES` with an empty
`timeSlots` array, producing the valid terminal result
`DAYS(1) -> TIMES(0) -> NO_SLOTS -> STOP`. This extends the evidence corpus;
under ADR-0011 it does not automatically add Berlin to the five
registry-enabled fallback profiles. Such admission requires an explicit
governance-reviewed configuration change and runtime validation.

A later review on the same day observed the same Berlin date with nine allowed
time entries (`15:15:00`–`17:15:00`) and `SLOTS_AVAILABLE`. The two retained
observations establish temporal variability, but do not identify its
provider-side cause.

Across the currently evidence-confirmed deployments—Madrid, Barcelona,
London, Milan, Valencia, and Berlin—successful HTTP `200` landing responses
exposed the public queue form and discovery proceeded through `DAYS` and
`TIMES`. This is a bounded evidence statement, not a protocol guarantee for
other deployments.

Later on 2026-08-01, owner-provided passive browser evidence confirmed
Toronto centre `46`, service `4`, one allowed date, and 11 allowed time
entries from `08:15:00` through `13:00:00` through the same terminal
`TIMES -> STOP` boundary. Frontend-source
evidence also identifies `form=check_services` as a public service preflight;
the supplied screenshots do not independently establish its live response.
This evidence expands the corpus without automatically changing Toronto's
registry capability or extending ADR-0010 browser enablement.

At that evidence checkpoint, the reviewed corpus contained seven deployments with the same
high-level bounded discovery sequence. Berlin is the retained reference case
showing that `NO_SLOTS` and `SLOTS_AVAILABLE` can both arise from the contents
of recognized `TIMES` responses without a different public execution branch.
This interpretation is limited to the reviewed evidence set.

On 2026-08-01, subsequent owner-provided reviews added Cologne centre `3`,
service `4`, and Bratislava centre `9`, service `4`, bringing the reviewed
public-contract corpus to nine deployments. On 2026-08-02, Berlin, Cologne,
Bratislava, and Toronto were promoted independently through an explicit
[governance review](governance/2026-08-02-public-discovery-profile-promotions.md).
Later on 2026-08-02, owner-provided Prague evidence confirmed centre `8`,
service `4`, one allowed date, and four allowed time entries. The project owner
approved `prague-v1` through an independent
[governance decision](governance/2026-08-02-prague-public-discovery-promotion.md),
bringing the reviewed and approved corpus to ten deployments without
generalizing the contract beyond them.
This is a governed capability change, not an automatic consequence of the
observations.

On 2026-08-02, a six-hour bounded release validation exercised Berlin,
Cologne, Bratislava, and Toronto alongside Madrid and Barcelona controls. The
confirmed browser-discovery executions either reached `TIMES` or stopped at a
recognized earlier `NO_SLOTS` boundary. No browser error or browser `UNKNOWN`
was recorded. Cologne remained `NO_SLOTS` throughout this window; this does
not contradict its earlier time-specific live availability evidence.
Kortrijk's separate candidate probe found no queue form or identifiers and did
not change capabilities. See the
[six-hour release validation](../research/dp-document/2026-08-02-seven-centre-6h-release-validation.md).

## ADR-0011: Trust Model for Evidence Collection and Capability Governance

**Status:** Accepted; normative

**Date:** 2026-08-01

### Context

The project collects runtime observations and research material from public
provider deployments. Automatically collected evidence can reveal candidate
service identifiers, selectors, response shapes, transports, or other
potential capabilities. Such evidence may be incomplete, temporary,
contradictory, or specific to one deployment version.

Treating automatically discovered evidence as authorization to change runtime
behavior would violate the evidence-first model. The project therefore needs
a stable trust boundary between facts, research material, interpretation,
trusted configuration, and runtime execution.

### Decision

> **Trust is declared, not inferred.**

The normative rules in this ADR are complemented by the
[Evidence Matrix](EVIDENCE_MATRIX.md), which records current deployment state
without becoming a source of runtime capabilities.

Trusted capabilities are declared explicitly through governance-controlled
configuration. Runtime observations and automatically collected evidence may
inform governance decisions, but they must never modify trusted capabilities
directly.

> Automatic collection may increase the evidence corpus, but it must never
> modify trusted provider capabilities.

### Trust layers

| Layer | Responsibility |
|---|---|
| Observation | Records immutable runtime facts |
| Candidate Artifact | Stores local, disposable material for investigation |
| Evidence Corpus | Preserves the logical body of retained evidence and interpretations |
| Governance Review | Evaluates evidence and authorizes capability changes |
| `providers.json` | Declares trusted provider capabilities |
| `provider_registry.py` | Loads and validates trusted configuration |
| Runtime Guard | Enforces the currently trusted contract and fails closed |

Observation and Candidate Artifact are separate outputs of a bounded runtime
observation. A Candidate Artifact does not extend Observation and is not
domain state or a source of truth.

### Evidence Corpus

**Evidence Corpus** is the logical body of retained observations, local
candidate artifacts, confirmed research records, and documented
interpretations available to governance review. It may contain evidence
collected at different times that supports mutually contradictory
interpretations.

The logical corpus is distributed by responsibility:

```text
Observations
    local immutable runtime store

Candidate Artifacts
    local disposable research-output

Confirmed Research Records
    sanitized repository documentation

Interpretations and Decisions
    ADRs, reviews, and registry history
```

Retained facts are not rewritten to make later interpretations appear
consistent. Important candidate evidence must receive a sanitized research
record through governance review before it becomes a durable basis for a
trusted capability.

### Governance Review and CI

Capability changes require an explicit and attributable governance decision:

```text
Governance Review
├── maintainer approval
├── reviewed PR
├── accepted RFC
└── documented project-owner decision

CI
└── verifies that the approved change satisfies policy
```

CI may validate configuration shape, evidence references, permitted
capabilities, and regression tests. CI does not interpret candidate evidence
or independently promote or demote capabilities.

### Governed Capability Evolution

Trusted provider capabilities evolve only through explicit governance
decisions. Automatically collected evidence may support those decisions but
never replaces them.

```text
Automatic process:
    EvidenceCorpus := EvidenceCorpus ∪ NewEvidence
    TrustedCapabilities := unchanged

Governance process:
    review(EvidenceCorpus)
    TrustedCapabilities := approved configuration
```

Promotion, revision, and demotion are all governance-controlled changes.
Neither repeated observations nor a frequently observed identifier such as a
service value can update `providers.json` automatically.

### Runtime Conservatism

Runtime Guard validates every execution against the currently trusted
provider contract and fails closed whenever that contract cannot be confirmed
from the current runtime response.

```text
Trusted capability
    ↓
Runtime validation
    ↓
Contract satisfied?
├── yes → continue within the confirmed boundary
└── no  → UNKNOWN or BLOCKED → STOP
```

An operational refusal does not revoke a capability. It stops only the current
execution and makes the contradictory or incomplete result available for
review.

| Runtime refusal | Governance change |
|---|---|
| Automatic | Explicit |
| Immediate | Reviewed |
| Fail-closed | Governance-controlled |
| Execution-scoped | Persistent configuration change |
| Does not edit capabilities | Promotes, revises, or removes capabilities |
| Produces Observation | Produces reviewed configuration history |

### Candidate Evidence Collection

Candidate evidence collection is one application of this trust model. A
provider without `public_discovery_profile` remains landing-only.

```text
HTTP 200
├── confirmed no-slots evidence → Observation → STOP
├── QUEUE_FORM_FOUND            → Candidate Artifact → STOP
└── maintenance or unknown HTML → UNKNOWN → STOP

HTTP BLOCKED
└── explicitly enabled bounded landing probe
    ├── QUEUE_FORM_FOUND → Candidate Artifact → STOP
    └── no confirmed form → Observation → STOP
```

`HTTP_200` alone never triggers candidate collection. The positive trigger is
`QUEUE_FORM_FOUND`. A blocked landing probe may run at most once for a new
`(provider_id, transport, page_hash)` key under a bounded cooldown. It may
inspect public landing-form structure but must not select a service or request
days or times.

Candidate details belong only under Git-ignored
`research-output/candidate-evidence/`. They must not contain CSRF values,
cookies, headers, raw HTML, screenshots, browser storage, CAPTCHA data,
fingerprints, or personal information.

### Evidence promotion

```text
Candidate Evidence
    ↓
Governance Review
    ↓
Documented Confirmation
    ↓
Explicit providers.json Change
    ↓
Discovery Profile
```

Every confirmed capability may be supported by earlier candidate evidence;
not every candidate becomes a confirmed capability.

### Non-goals

This decision does not introduce or permit:

- automatic capability promotion;
- automatic capability demotion;
- automatic registry modification;
- automatic service selection from candidate evidence;
- expansion of Observation into a research dump;
- booking or reservation;
- identity verification;
- CAPTCHA interaction;
- fingerprint generation;
- an additional database, event bus, plugin system, or distributed service.

### Consequences

- `providers.json` remains the declarative source of trusted provider
  capabilities;
- `provider_registry.py` remains a loader and validator, not a source of
  inferred capabilities;
- runtime may always stop when current evidence does not satisfy a confirmed
  contract;
- candidate artifacts remain local, disposable, and excluded from source
  control;
- future provider, transport, notification, and adapter decisions must refer
  to this trust model rather than define automatic promotion rules;
- this ADR should change only if a logical contradiction is found or a new
  class of architectural decision cannot be expressed by its principles.

### Axioms

> **Trust is declared, not inferred.**

```text
Evidence accumulates.

Interpretations evolve.

Trusted capabilities are governed.

Runtime validates every execution.

Runtime fails closed whenever validation fails.
```

## ADR-0012: Evidence-First Notification Derivation and Output Isolation

**Status:** Proposed

**Date:** 2026-08-02

### Context

The implemented runtime produces immutable Observations but does not send
Telegram, email, push, webhook, or other external notifications. A future
notification subsystem must communicate useful public facts without becoming
a control path into provider monitoring, Runtime Guard, trusted capabilities,
or governance.

Direct monitor-to-channel delivery would couple provider execution to network
delivery, make transient availability difficult to confirm, and give channel
adapters access to more runtime data than they require. It would also obscure
why a message was sent and which policy version authorized it.

ADR-0011 governs how evidence may support trusted capabilities. The output
architecture needs the corresponding rule for external communication:

> **Output capabilities are governed with the same discipline as runtime
> capabilities, while remaining an independent architecture.**

### Decision

Notification processing is a one-way, evidence-first Output Pipeline:

```text
Committed Observation
    -> Notification Candidate
    -> versioned Policy Set
    -> Notification Decision Trace
    -> Confirmed Notification Event
    -> Delivery Job
    -> Delivery Adapter
    -> Delivery Audit
```

The Input Pipeline terminates at immutable Observation. The Output Pipeline
may read committed source facts but has no control path back into a provider,
monitor, transport, Runtime Guard, Observation, `providers.json`, the Evidence
Matrix, or governance state.

Notifications are outputs only. They never promote knowledge, provider
capabilities, or notification capabilities automatically.

### Output layers

| Layer | Responsibility |
|---|---|
| Observation reader | Reads committed immutable source facts through a durable cursor |
| Event builder | Produces a sanitized Notification Candidate from allowlisted facts |
| Confirmation policy | Decides whether later natural observations confirm or invalidate the candidate |
| Deduplication policy | Suppresses or aggregates equivalent confirmed events |
| Priority policy | Classifies urgency independently from audience |
| Privacy policy | Rejects envelopes outside the public-data allowlist |
| Routing policy | Selects audience, channel, and destination alias |
| Notification queue | Persists immutable delivery jobs with leases and bounded retries |
| Delivery adapter | Translates a normalized envelope to one external channel |
| Audit store | Records operational handling without changing logical decisions |

### Policy Sets

`notification_profiles.json` is the proposed declarative source of trusted
notification policy. It remains independent from `providers.json` and contains
no credentials.

A Policy Set references independently versioned confirmation,
deduplication, priority, privacy, and routing policies. Developer, research,
and future public notification profiles may use different Policy Sets. Every
logical decision records the Policy Set ID, version, and safe normalized hash
that produced it.

Policy changes do not change event schema versions unless the structure or
meaning of a persisted contract changes.

### Confirmation without feedback

> **Policies consume observations but never schedule them.**

Confirmation may require a configurable number of consecutive observations,
a minimum duration, a maximum window, a required discovery stage, and reset
states. Provider-specific notification-policy overrides may exist only in the
separate notification configuration.

The Output Pipeline must not request an early provider check, change polling
frequency, start Playwright, or otherwise create a notification-to-runtime
feedback loop. A candidate that is not confirmed by naturally occurring
observations expires or is discarded.

### Decisions, provenance, and audit

Notification Candidate, Notification Decision, Confirmed Notification Event,
Notification Provenance, Delivery Job, Delivery Result, and Notification Audit
Record are separate immutable, schema-versioned contracts.

Notification Decision records why a versioned policy accepted, rejected,
suppressed, or deferred a candidate. Decisions for one candidate and one
Policy Set share a `decision_trace_id` and deterministic sequence number.
Notification Audit records what infrastructure later did. An accepted routing
decision does not imply successful delivery, and a delivery failure does not
change the logical event.

Every externally deliverable event must retain sanitized provenance linking
it to source Observation IDs, its confirmation interval, and every referenced
policy version. Provenance never contains raw provider payloads, browser state,
credentials, or destination identifiers.

### Decision reproducibility

Given retained source facts, their deterministic ordering, the referenced
Policy Set, evaluation time, and relevant retained notification decision
state, the logical Decision Trace must be reproducible without provider
runtime or delivery infrastructure.

Replay compares normalized logical results. Newly generated IDs, test-run
timestamps, Telegram responses, and operational audit records are not part of
the reproducible decision result.

### Coordinator and adapters

> **The Notification Coordinator performs orchestration only.**

It may order policy evaluation, persist decisions, advance its processing
cursor, and enqueue accepted routes. It must not contain event-specific,
provider-specific, priority, privacy, routing, channel, or message-formatting
rules.

Delivery adapters receive only normalized, privacy-validated Notification
Envelopes. Telegram is the first planned adapter, not part of the domain
model. A Telegram adapter must not import Observation, provider configuration,
provider monitors, Runtime Guard, Playwright, or governance state.

### Privacy and security boundary

Allowlisted outbound facts are limited to sanitized public centre and service
labels, normalized state and discovery stage, observation time, aggregate
availability counts, earliest/latest public time, an official public URL, and
coarse reason codes.

Notification contracts, jobs, logs, audit records, and outbound payloads must
never contain cookies, CSRF values, request or response headers, raw HTML,
browser storage, browser-profile paths, HAR or trace data, screenshots, phone
numbers, OTP, CAPTCHA data, identity data, booking payloads, bot tokens, raw
destination identifiers, or arbitrary exception bodies.

Privacy validation occurs before queue insertion and again before delivery.
Unknown schemas, Policy Sets, policies, event types, or fields fail closed and
produce only a sanitized local refusal record.

### Queue boundary

The initial planned queue has a `NotificationQueue` protocol with in-memory
contract-test and SQLite implementations. It supports priority ordering,
deduplication, bounded leases, stale-lease protection, retry backoff, and
terminal failure.

DiagnosticQueue is not reused: diagnostics and notifications have different
domain payloads and lifecycles. A separate `QueueStorage` abstraction is
deferred until a second persistent notification implementation demonstrates
that it is necessary.

### Source-fact boundary

Provider notification candidates derive from Observation. `RUN_COMPLETED`,
`RESEARCH_SUMMARY_GENERATED`, `GOVERNANCE_REMINDER`, and similar events are not
provider Observations and must not be fabricated as such. They require a
separately reviewed immutable Operational Fact contract before implementation.

### Non-goals

This decision does not implement or authorize:

- Telegram or any other external API call;
- a runtime notification coordinator, queue, worker, or adapter;
- user subscriptions or public notification destinations;
- runtime hooks or changes to Observation;
- provider checks initiated by notification policy;
- changes to `providers.json`, the Evidence Matrix, or trusted capabilities;
- booking, identity verification, CAPTCHA interaction, or browser execution;
- an event bus, microservice split, plugin framework, Redis, or PostgreSQL.

### Consequences

- notification implementation can begin only after this ADR is accepted;
- the first implementation milestone is offline immutable contracts, schema
  validation, policy loading, decision replay, and architecture tests;
- SQLite queue, worker, and a developer-only Telegram adapter follow only
  after the offline milestone passes;
- runtime integration follows bounded offline and adapter validation;
- end-user notifications require a separate privacy and governance review;
- every external message must be explainable from retained facts, versioned
  policies, a complete Decision Trace, and delivery audit history.

### Output invariants

```text
Observations are immutable inputs to the Output Pipeline.

Candidates do not authorize delivery.

Policies consume observations but never schedule them.

Every confirmation is an explicit versioned decision.

Priority and audience are independent dimensions.

Coordinator performs orchestration only.

Adapters consume envelopes but never Observations.

Delivery results never alter source facts.

Notification output never modifies trusted capabilities.

Every external message is traceable to retained facts and policies.
```
