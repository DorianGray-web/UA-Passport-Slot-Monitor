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
