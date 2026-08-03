# SQLite Delivery Job Persistence Governance Authorization

**Decision:** Authorized

**Decision date:** 2026-08-03

**Decision authority:** Project owner

## Subject

A bounded implementation slice under
[ADR-0012](../DECISIONS.md#adr-0012-evidence-first-notification-derivation-and-output-isolation).

## Authorized implementation scope

- immutable `NotificationDeliveryJob`;
- local SQLite Delivery Job Store;
- `enqueue`, `claim`, `complete`, and `fail` state transitions;
- bounded retry metadata, priority ordering, caller-supplied idempotent
  `dedup_key`, leases, stale-lease protection, and crash-safe transactions;
- persistence tests.

The immutable job and mutable delivery state are stored separately. Lease data
belongs to persistence state and never changes the job. Priority is decided
before persistence; SQLite only orders the supplied priority. The `dedup_key`
originates from the logical notification event and is never derived by SQLite.

## Explicitly not authorized

- Telegram or another Delivery Adapter;
- delivery workers or schedulers;
- runtime hooks, provider changes, or Observation access;
- notification generation or formatting;
- network communication, credentials, secrets, or environment-specific
  delivery.

## Decision history

- 2026-08-03: project owner authorized this persistence-only slice.
