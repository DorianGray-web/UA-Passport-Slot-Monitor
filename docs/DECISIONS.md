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

**Status:** Accepted

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
