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

### Changed

- Updated the project status from conceptual design to research, user validation, and provider integration prototyping.
- Refined the provider strategy for public applications that require a normal browser session.
- Clarified that CAPTCHA and anti-bot challenges require manual intervention and must not be bypassed.
- Clarified that blocked, unknown, invalid, or incomplete responses must never be interpreted as `NO_SLOTS`.
- Expanded the roadmap into verifiable provider-research and MVP milestones.

### Research

- Confirmed that direct HTTP requests may be rejected while the public appointment page remains accessible through a normal browser session.
- Confirmed that the public client application exposes the general workflow for service selection, available days, available times, and manual registration.
- Identified capture validation as a required boundary before availability data can be normalized.

### Planned

- Confirm live availability responses.
- Define the normalized provider response model.
- Implement the first Kortrijk provider adapter.
- Implement safe polling, backoff, and duplicate-subscription handling.
- Implement manual challenge-intervention and notification flows.

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
