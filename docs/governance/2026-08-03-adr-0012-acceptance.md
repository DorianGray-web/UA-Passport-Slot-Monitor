# ADR-0012 Governance Decision

**Decision:** Accepted

**Decision date:** 2026-08-03

**Decision authority:** Project owner

## Subject

[ADR-0012: Evidence-First Notification Derivation and Output Isolation](../DECISIONS.md#adr-0012-evidence-first-notification-derivation-and-output-isolation)

## Decision

The project owner accepted ADR-0012 after review against ADR-0011,
Architecture, Security, Privacy, and Release Policy boundaries.

## Authorized implementation scope

- immutable `NotificationCandidate`, `NotificationDecision`,
  `ConfirmedNotificationEvent`, provenance, and append-only `DecisionTrace`
  contracts;
- fail-closed loading of credential-free, versioned Policy Sets;
- pure offline confirmation replay;
- contract, policy-loading, replay, and architecture tests.

## Explicitly not authorized

- Telegram or another external API;
- notification queues, workers, or delivery adapters;
- runtime or `monitor_runner.py` integration;
- provider or `providers.json` changes;
- notification-triggered observations;
- booking, identity, CAPTCHA, or browser activity.

## Decision history

- 2026-08-02: ADR authored as `Proposed`.
- 2026-08-03: project owner accepted ADR-0012 and authorized the offline
  domain slice above.
