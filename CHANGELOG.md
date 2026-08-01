# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog. The project follows a documentation-first development approach.

This changelog tracks implementation milestones and significant documentation, architecture, research, and governance changes.

## [Unreleased]

### Added

- Added a run-scoped Research Summary Generator that derives transport,
  availability, timeline, behaviour, and per-provider statistics from the
  immutable Observation store.
- Added automatic Markdown report generation when the orchestrator is stopped
  after a long run, with a configurable minimum-duration threshold.
- Kept observed facts separate from interpretation and explicitly reports the
  enforced identity, CAPTCHA, and booking boundary.

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
  `london-research-v1`, and `milan-research-v1`; the remaining centres stay
  landing-only.
- Made unexpected Madrid days/times statuses, payload shapes, fields, and
  values fail closed as `UNKNOWN`.
- Kept HTTP preferred while allowing one non-retrying persistent-browser
  attempt per blocked cycle when the experimental fallback is enabled.
- Expanded Git exclusions for browser state, captures, network artifacts,
  cookies, tokens, storage, HAR/trace/log files, runtime databases, sessions,
  environment files, caches, and Site Investigator runtime output.

### Research

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
