# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog. The project follows a documentation-first development approach.

This changelog tracks implementation milestones and significant documentation, architecture, research, and governance changes.

## [Unreleased]

### Documentation

- Recorded the project-owner governance authorization for the bounded SQLite
  Delivery Job Persistence slice under ADR-0012.

- Recorded owner-provided Chisinau live evidence confirming centre `45`,
  service `4`, 25 allowed dates, a non-empty `TIMES` response, and the bounded
  `LANDING -> DAYS -> TIMES -> STOP` public contract.
- Recorded the project-owner governance decision approving the independently
  reviewed `chisinau-v1` public-discovery capability.
- Recorded owner-provided Varna live evidence confirming centre `43`, service
  `4`, one allowed date, ten allowed time entries, and the bounded
  `LANDING -> DAYS -> TIMES -> STOP` public contract.
- Recorded the project-owner governance decision approving the independently
  reviewed `varna-v1` public-discovery capability.
- Added and accepted ADR-0012, defining evidence-first notification derivation,
  versioned Policy Sets, immutable Decision Traces, decision reproducibility,
  privacy validation, output isolation, and the orchestration-only Coordinator
  invariant.
- Added the proposed Notification Architecture for a one-way
  `Observation -> Candidate -> Decision -> Confirmed Event -> Delivery -> Audit`
  Output Pipeline with Telegram as a future replaceable adapter rather than a
  runtime dependency.
- Added independently versioned notification event contracts and explicit
  separation between logical Notification Decisions, provenance, delivery
  jobs/results, and operational audit records.
- Added a draft JSON Schema for credential-free Policy Sets, confirmation and
  deduplication policies, provider-specific notification overrides, privacy
  allowlists, and audience/channel routing profiles.
- Added the Notification Test Strategy covering contract, policy, Decision
  Replay, integration, architecture, and privacy-regression tests.
- Extended the Release Policy Traceability gate so any future externally
  deliverable event must be reproducible from retained facts, logical decision
  state, and the referenced versioned Policy Set.
- Recorded the project-owner governance decision authorizing only the offline
  notification-domain slice.
- Documented that the initial offline notification-domain slice had no queue;
  the later independently authorized persistence slice still has no runtime
  integration, worker, adapter, Telegram API call, provider change, or
  external message.
- Recorded owner-provided Prague live evidence confirming centre `8`, service
  `4`, one allowed date, four allowed time entries from `11:45:00` through
  `12:45:00`, and the bounded `LANDING -> DAYS -> TIMES -> STOP` contract.
- Recorded the project-owner governance decision approving the independently
  reviewed `prague-v1` public-discovery capability.
- Recorded sanitized Kortrijk candidate evidence from a later bounded probe:
  public queue form, centre `48`, service option `4`, and date/time selectors.
  The probe stopped at `LANDING`; no service was selected and no capability was
  promoted.

### Added

- Added the immutable `NotificationDeliveryJob` and privacy-bounded envelope
  contracts plus a local SQLite store with separate mutable delivery state,
  caller-supplied idempotent deduplication keys, priority ordering, leases,
  stale-lease protection, bounded retry metadata, and crash-safe transactions.
- Added persistence tests without adding workers, adapters, runtime hooks,
  Observation access, notification generation, network communication, or
  environment-specific delivery.

- Promoted the existing Chisinau deployment from landing-only research to the
  twelfth evidence-gated discovery profile without adding identity, CAPTCHA,
  fingerprint, or booking logic.
- Added Varna as the thirteenth independently supervised deployment and the
  eleventh evidence-gated discovery profile, reusing the shared `CityMonitor`
  protocol without adding identity, CAPTCHA, fingerprint, or booking logic.
- Added Prague as the twelfth independently supervised deployment and the
  tenth evidence-gated discovery profile, reusing the shared `CityMonitor`
  protocol without adding identity, CAPTCHA, fingerprint, or booking logic.
- Added the Architecture Protection CI workflow using the existing unittest
  suite, compileall, static boundary and notification-layer direction guards,
  and tracked repository hygiene checks.
- Added an extensible `tools/architecture/` checker package. Notification
  guards protect the offline domain without authorizing notification runtime.
- Added the offline notification domain: immutable Candidate, Decision,
  Confirmed Event, provenance, and append-only Decision Trace contracts;
  fail-closed Policy Set loading; pure confirmation replay; and replay tests.

## [0.3.0] - 2026-08-02

### Added

- Added a permanent Evidence Matrix covering every configured deployment and
  separating observation, contract confirmation, comparative validation,
  governance approval, and runtime capability.
- Added a capability-promotion checklist that makes `providers.json` changes
  the reviewed conclusion of the evidence lifecycle rather than an automatic
  consequence of observation.
- Added a run-scoped Research Summary Generator that derives transport,
  availability, timeline, behaviour, and per-provider statistics from the
  immutable Observation store.
- Added automatic Markdown report generation when the orchestrator is stopped
  after a long run, with a configurable minimum-duration threshold.
- Kept observed facts separate from interpretation and explicitly reports the
  enforced identity, CAPTCHA, and booking boundary.
- Added normative ADR-0011, defining the project trust model for evidence
  collection, governance-controlled capabilities, and fail-closed runtime
  validation.
- Added an opt-in, cooldown-bound candidate landing probe for Berlin and
  Kortrijk. It records sanitized local form candidates, never selects a
  service, and stops at `LANDING`.
- Extended the Research Summary Generator to report candidate landing probes
  separately from confirmed Playwright discovery runs.
- Added Cologne as the eleventh independently supervised deployment and
  approved `cologne-v1` for centre `3`, service `4`.
- Added four independent governance approvals for Berlin, Cologne,
  Bratislava, and Toronto public discovery profiles.
- Added the normative Release Policy with independent technical, governance,
  and traceability gates.
- Added the v0.3.0 Release Readiness Report recording passing technical,
  governance, traceability, operational, hygiene, and documentation gates.
- Added a sanitized seven-centre 12-hour runtime validation note.
- Added a sanitized seven-centre six-hour release-validation note covering
  the four newly governed profiles, two established controls, and the
  landing-only Kortrijk candidate probe.

- Started the first provider feasibility study using the DP Document service center in Kortrijk, Belgium.
- Started browser-assisted capture for provider research.
- Added research requirements for detecting access restrictions, CAPTCHA, challenge pages, and incomplete captures.
- Began analysis of the publicly delivered client application and its appointment workflow stages.
- Documented the first provider research scope and the generalized DP Document queue workflow.
- Added independent queue monitors for Berlin, Germany, and Bratislava,
  Slovakia, using the same HTTP-only landing-page classification model as the
  Kortrijk prototype.
- Added `monitor_runner.py` to start, supervise, restart, and stop the
  Kortrijk, Berlin, and Bratislava monitors as separate processes.
- Added separate provider logs and a system-only orchestrator log.
- Added append-only JSON Lines monitoring metadata for cross-centre analysis,
  including UTC timestamp, provider, state, transport, diagnostic status,
  HTML-change status, response time, and HTTP status.
- Added offline regression coverage for the multi-provider contracts and
  standardized metadata records.
- Added immutable, schema-versioned Observation and DiagnosticDecision
  contracts with transactional SQLite outbox persistence.
- Added backend-agnostic DispatchTarget and DiagnosticQueue interfaces,
  in-memory contract-test support, and a persistent SQLite implementation.
- Added a separately supervised diagnostic worker with priority ordering,
  cooldown, deduplication, bounded leases, stale-worker protection, and
  expired-lease recovery.
- Added configuration-driven Madrid, London, Milan, Toronto, and Chisinau
  monitor entrypoints using the existing shared city monitor.
- Added per-city research priority, enablement, and active/control observation
  group configuration for the multi-centre research sample.
- Extended the orchestrator to supervise all eight configured centres as
  independent processes.
- Added strict Madrid classifiers for the confirmed public `days` and
  `timeSlots` JSON schemas.
- Added Madrid-only runtime discovery through `LANDING -> DAYS -> TIMES`,
  terminating immediately after public time-slot collection.
- Added Observation schema v3 fields for date count, allowed time-entry
  count, and earliest/latest available time.
- Added Barcelona as the ninth independently supervised provider with
  separate log, state, and JSONL Observation output.
- Added the evidence-gated `barcelona-v1` profile for confirmed public
  `LANDING -> DAYS -> TIMES -> STOP` discovery using centre `41` and service
  `4`.
- Added an opt-in persistent Playwright discovery transport for Madrid and
  Barcelona research runs after HTTP `BLOCKED`.
- Extended the explicitly enabled experimental Playwright discovery transport
  to the evidence-confirmed London and Milan research profiles, while
  preserving HTTP-first selection and the terminal `TIMES` boundary.
- Added confirmed London centre `47` and Milan centre `4` configurations for
  service `4` without adding identity, CAPTCHA, or booking behavior.
- Added sanitized mixed-transport request traces for HTTP/Playwright
  completion and timing analysis without changing Observation schema v3.
- Added Valencia as the tenth independently supervised centre and as the fifth
  evidence-gated public-discovery profile (`ServiceCenterId=7`,
  `ServiceId=4`).
- Added a five-centre Madrid, Barcelona, London, Milan, and Valencia research
  cohort for bounded HTTP-first transport comparison.

### Changed

- Updated the project status from conceptual design to research, user validation, and provider integration prototyping.
- Refined the provider strategy for public applications that require a normal browser session.
- Clarified that CAPTCHA and anti-bot challenges require manual intervention and must not be bypassed.
- Clarified that blocked, unknown, invalid, or incomplete responses must never be interpreted as `NO_SLOTS`.
- Expanded the roadmap into verifiable provider-research and MVP milestones.
- Standardized provider log names under the project-level `logs/` directory.
- Added local `metadata/` output to the Git ignore policy.
- Replaced synchronous monitor-to-backend calls with asynchronous outbox
  dispatch so diagnostic execution cannot block provider monitoring.
- Removed implicit and synchronous Playwright execution from normal DP
  Document monitoring. Browser execution remains disabled by default;
  explicitly enabled confirmed research profiles may use the separate
  experimental fallback after HTTP `BLOCKED`.
- Added independent MonitorProvider and future BookingProvider boundaries so
  fingerprint generation cannot become a monitoring dependency.
- Added an evidence-first landing state machine with typed Evidence,
  DiscoveryStage, transition guards, and sanitized RequestTrace.
- Refined landing classification so an embedded booking hCaptcha does not
  block public queue discovery when positive form and CSRF evidence exists.
- Added support for the confirmed `qlogicFormTotoro` form configuration,
  `center` field, and selected `service` option without persisting CSRF data.
- Added configurable 30-second provider startup offsets to avoid an
  eight-centre initial request burst.
- Added `MONITOR_PROVIDER_CITIES` for temporary research cohorts without
  editing the provider registry.
- Added a one-hour minimum cooldown after four consecutive HTTP `BLOCKED`
  observations.
- Upgraded immutable Observation to schema v2; request count is derived from
  trace length rather than persisted separately.
- Upgraded immutable Observation to schema v3 for normalized public
  availability while retaining analysis-safe request traces.
- Generalized the strict Madrid response classifiers into confirmed DP
  Document days/times classifiers shared only by explicitly approved evidence
  profiles.
- Enabled full public discovery for `madrid-v1`, `barcelona-v1`,
  `london-research-v1`, `milan-research-v1`, `valencia-v1`, `berlin-v1`,
  `toronto-v1`, `cologne-v1`, and `bratislava-v1`; Kortrijk and Chisinau stay
  landing-only.
- Replaced the legacy Kortrijk implementation with the shared `CityMonitor`
  entrypoint while preserving candidate-only, no-service-selection behaviour.
- Distinguished orchestrator runtime from Observation coverage in research
  summaries and now use runtime duration for automatic report thresholds.
- Synchronized the confirmed discovery-profile allowlist with the governed
  Berlin, Cologne, Bratislava, and Toronto registry profiles.
- Made unexpected Madrid days/times statuses, payload shapes, fields, and
  values fail closed as `UNKNOWN`.
- Kept HTTP preferred while allowing one non-retrying persistent-browser
  attempt per blocked cycle when the experimental fallback is enabled.
- Expanded Git exclusions for browser state, captures, network artifacts,
  cookies, tokens, storage, HAR/trace/log files, runtime databases, sessions,
  environment files, caches, and Site Investigator runtime output.

### Research

- Recorded owner-provided Berlin live evidence confirming centre `2`, service
  `4`, and the bounded public `LANDING -> DAYS -> TIMES -> STOP` workflow.
- Recorded the Berlin terminal case `DAYS(1) -> TIMES(0) -> NO_SLOTS`, which
  confirms that `NO_SLOTS` can be a valid post-discovery result and is not
  limited to landing-page classification.
- Recorded a later Berlin observation for the same date in which `TIMES`
  returned 9 allowed entries from `15:15:00` through `17:15:00`, transitioning
  to `SLOTS_AVAILABLE`; response labels reported 61 free appointments across
  those entries.
- Documented that Madrid, Barcelona, London, Milan, Valencia, and Berlin now
  share the same high-level public discovery contract across the currently
  evidence-confirmed deployments. This evidence is not generalized to other
  deployments and does not itself change registry capabilities.
- Recorded owner-provided Toronto live evidence confirming centre `46`,
  service `4`, one allowed date, 11 allowed time entries from `08:15:00`
  through `13:00:00`, and the bounded public
  `LANDING -> DAYS -> TIMES -> STOP` workflow. The response labels reported 32
  free appointments across those entries.
- Recorded frontend-source evidence for the separate public
  `form=check_services` preflight while keeping its live response distinct
  from the browser-observed `days` and `timeSlots` responses.
- Added a nine-deployment comparison showing the shared evidence-confirmed
  `LANDING -> DAYS -> TIMES -> STOP` sequence and using Berlin as the reference
  case for `NO_SLOTS`/`SLOTS_AVAILABLE` variability within the same public
  contract.
- Completed the six-hour bounded release validation: 241 HTTP-first cycles,
  213 blocked HTTP landings, 202 confirmed Playwright discovery runs, 117
  `TIMES` completions, 85 recognized earlier `NO_SLOTS` stops, and zero
  browser errors or browser `UNKNOWN` results.
- Recorded that Cologne remained `NO_SLOTS` in all 38 observations during the
  six-hour window despite earlier live slot evidence, while Kortrijk yielded
  no candidate identifiers and remained landing-only.
- Recorded owner-provided Valencia live evidence confirming centre `7`,
  service `4`, the public `form=days` and date-dependent `form=times` flow,
  and response arrays compatible with the strict confirmed classifiers.

- Validated passive public availability discovery across Madrid, Barcelona,
  London, and Milan during a 3h 57m run: all 79 Playwright fallbacks reached
  the confirmed `TIMES` boundary and reported `SLOTS_AVAILABLE`, with zero
  browser errors, unexpected browser `UNKNOWN` results, CAPTCHA interactions,
  identity-data interactions, or booking actions.
- Recorded that 23 HTTP `200` observations remained `UNKNOWN` in the current
  runtime while 79 HTTP `403` observations triggered successful browser
  fallback. This is evidence about current transport/classifier coverage, not
  proof that public `days`/`times` requests are inherently impossible via HTTP.

- Confirmed that direct HTTP requests may be rejected while the public appointment page remains accessible through a normal browser session.
- Confirmed that the public client application exposes the general workflow for service selection, available days, available times, and manual registration.
- Identified capture validation as a required boundary before availability data can be normalized.
- Established an offline-validated multi-centre observation baseline for later
  timing and correlation analysis; subsequent entries below record the later
  bounded live validations.
- Confirmed in DP Document frontend 7.34.2 that pre-authentication queue
  discovery uses `form=days` and `form=times` without browser fingerprinting.
- Confirmed that embedded ThumbmarkJS module 708 is used only by booking
  submission methods and makes no observed API call during queue discovery.
- Recorded user-provided passive live observations from Bratislava and Milan
  on 2026-07-30. They support separate date and time discovery stages but do
  not establish identical deployment contracts or automated monitor
  validation.
- Recorded owner-reported findings that London and Madrid expose comparable
  queue stages while Toronto and Chisinau expose `NO_SLOTS` landing pages.
- Added an active/control multi-centre observation plan for comparative
  platform research.
- Compared the landing-only runtime with the documented pre-identity
  `service -> dates -> times` workflow.
- Added a passive public-page browser probe that performs no clicks, form
  submissions, identity actions, or booking actions.
- Recorded a 2026-07-31 Bratislava `BLOCKED` capture and documented that it
  cannot prove the presence or absence of calendar data.
- Proposed fixture-gated days/times classifiers and an optional immutable
  Observation schema v3 extension without implementing booking or identity
  verification.
- Documented an approximately eight-hour Madrid, London, and Milan HTTP
  runtime validation with stable process supervision, Observation recording,
  startup delays, and repeated-block cooldown behavior.
- Confirmed that unchanged `BLOCKED -> BLOCKED` observations with identical
  Cloudflare evidence do not generate additional diagnostic events.
- Recorded intermittent Madrid and Milan HTTP `200` responses containing
  `QUEUE_FORM_FOUND`, `SERVICE_CENTER_FOUND`, and `UNRECOGNIZED_HTML`
  evidence. These successful public-form responses remain correctly
  classified as `UNKNOWN` pending confirmed classifier coverage.
- Confirmed that the next monitoring research milestone is fixture-backed
  `DAYS` and `TIMES` classification; identity verification, CAPTCHA
  interaction, and booking remain out of scope.
- Independently validated one bounded Barcelona fallback cycle: HTTP landing
  `403`, persistent Playwright landing `200`, confirmed `DAYS`, confirmed
  `TIMES`, then immediate stop.
- Recorded 12 available Barcelona dates and 325 allowed public time entries
  between 10:00 and 18:30 in an immutable `transport=playwright` Observation.

### Documentation

- Reconciled architecture, provider, roadmap, concept, and user-flow documents
  with the implemented landing-only monitor runtime and the separate HTTP
  `days`/`times` adapter boundary.
- Marked subscriptions, notifications, booking, fingerprinting, complete
  discovery normalization, and centre-specific live validation according to
  their actual status.
- Added ADR-0009 to retain independent city entrypoints during live research
  and define the criteria for a later registry-driven generic monitor.

## [0.1.1] - 2026-07-28

### Research

- Completed a continuous 24-hour Kortrijk queue observation.
- Confirmed that direct HTTP observation is intermittently available but
  frequently challenged.
- Confirmed the need for a passive Playwright fallback for reliable rendered
  state classification.
- Documented browser-observation boundaries: no fingerprint spoofing, proxy or
  IP rotation, automated CAPTCHA solving, booking, or form submission.
- Verified temporary `BLOCKED` detection, progressive backoff, and automatic
  recovery to `NO_SLOTS`.

These findings describe the earlier page-level experiment. Frontend 7.34.2
call-site analysis later superseded Playwright fallback for normal monitoring;
browser automation is now restricted to diagnostics and research.

## [0.1.0] - 2026-07-20

### Added

#### Project foundation

- Documentation-first development approach adopted.
- Privacy-first architecture established.
- Initial project principles documented.

#### Project documentation

- Project concept
- Architecture
- Roadmap
- Project decisions

#### Project policies

- Privacy policy
- Security policy
- Documentation language policy

#### Community

- Contributing guidelines
- Localized user documentation

### Changed

- Documentation reorganized.
- Project structure improved.

### Community engagement

- Public user survey launched.
- Initial community feedback collected.

### Notes

The project remained in the research and validation stage. No production implementation existed at this release.
