# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog. The project follows a documentation-first development approach.

This changelog tracks implementation milestones and significant documentation, architecture, research, and governance changes.

## [Unreleased]

### Added

- Started the first provider feasibility study using the DP Document service center in Kortrijk, Belgium.
- Started browser-assisted capture for provider research.
- Added research requirements for detecting access restrictions, CAPTCHA, challenge pages, and incomplete captures.
- Began analysis of the publicly delivered client application and its appointment workflow stages.
- Documented the first provider research scope and the generalized DP Document queue workflow.
- Added independent queue monitors for Berlin, Germany, and Bratislava,
  Slovakia, using the same HTTP-first and passive Playwright-fallback model as
  the Kortrijk research monitor.
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
- Removed Playwright from normal DP Document monitoring. Blocked HTTP
  observations remain `BLOCKED` and may request separate diagnostics.
- Added independent MonitorProvider and future BookingProvider boundaries so
  fingerprint generation cannot become a monitoring dependency.
- Added an evidence-first landing state machine with typed Evidence,
  DiscoveryStage, transition guards, and sanitized RequestTrace.
- Upgraded immutable Observation to schema v2; request count is derived from
  trace length rather than persisted separately.
- Expanded Git exclusions for browser state, captures, network artifacts,
  cookies, tokens, storage, HAR/trace/log files, runtime databases, sessions,
  environment files, caches, and Site Investigator runtime output.

### Research

- Confirmed that direct HTTP requests may be rejected while the public appointment page remains accessible through a normal browser session.
- Confirmed that the public client application exposes the general workflow for service selection, available days, available times, and manual registration.
- Identified capture validation as a required boundary before availability data can be normalized.
- Established an offline-validated multi-centre observation baseline for later
  timing and correlation analysis. Live Berlin and Bratislava behavior remains
  unverified.
- Confirmed in DP Document frontend 7.34.2 that pre-authentication queue
  discovery uses `form=days` and `form=times` without browser fingerprinting.
- Confirmed that embedded ThumbmarkJS module 708 is used only by booking
  submission methods and makes no observed API call during queue discovery.

### Planned

- Confirm live availability responses.
- Define the normalized provider response model.
- Complete live verification of the initial Kortrijk observation adapter.
- Implement duplicate-subscription handling on top of the existing polling and
  backoff behavior.
- Implement manual challenge-intervention and notification flows.
- Run authorized live verification for the Berlin and Bratislava monitors,
  including HTTP days/times classification, blocked-state recovery, and
  provider-specific page markers.
- Add analysis tooling for time-of-day HTML changes, simultaneous centre
  updates, and delays between HTML changes and confirmed slot availability.

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
