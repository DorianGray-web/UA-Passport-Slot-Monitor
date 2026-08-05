# Notification Worker Verification

**Date:** 2026-08-04
**Scope:** the governance-authorized local Worker Execution slice under
[ADR-0012](../DECISIONS.md#adr-0012-evidence-first-notification-derivation-and-output-isolation).

## Result

**PASS.** The local execution engine processes one persisted immutable
`NotificationDeliveryJob` through the Store API and a deterministic in-memory
fake adapter. It adds no external delivery or runtime integration.

## Implemented scope

- caller-driven `NotificationDeliveryWorker.run_once`;
- immutable `DeliveryResult` with `SUCCESS`, `RETRYABLE_FAILURE`, and
  `PERMANENT_FAILURE` outcomes;
- `claim -> deliver(job) -> complete/fail` persistence transitions;
- bounded retry scheduling and terminal failure handling;
- local in-memory fake adapter;
- persistence-transition and immutable-job tests;
- static architecture protection for prohibited Worker imports.

## Explicit non-goals

This verification does not authorize or implement:

- Telegram or any other external adapter or network call;
- scheduler, background loop, multiprocessing, or runtime hook;
- `monitor_runner` integration, provider changes, or direct Observation access;
- notification generation, confirmation-policy evaluation, or formatting;
- secrets, destination resolution, subscriptions, or user-facing delivery.

## Verification matrix

| Area | Result | Evidence |
|---|---|---|
| Local worker tests | PASS | 4 worker tests passed. |
| Queue persistence tests | PASS | 8 queue tests passed. |
| Full unit suite | PASS | 95 `unittest` cases passed. |
| Python compilation | PASS | `compileall` and `py_compile` passed for worker files. |
| Boundary protection | PASS | Static guard rejects Worker imports of policy, replay, provider, runner, and diagnostic modules. |
| Layer direction | PASS | Notification layer-direction guard passed. |
| Repository hygiene | PASS | Hygiene guard passed for 161 tracked files. |
| Diff integrity | PASS | `git diff --check` passed. |

## Architecture boundaries reviewed

- The Worker imports `NotificationDeliveryJob`, the Store API, and its local
  `DeliveryPort` contract only; it does not import decisions, policies,
  replay, Observations, providers, `monitor_runner`, or diagnostics.
- The Worker contains no `sqlite3` connection or SQL. SQLite remains entirely
  inside `SQLiteDeliveryJobStore`.
- `DeliveryPort.deliver(job)` receives only the immutable job and returns a
  small sanitized result. It receives no Store, connection, lease token,
  claim timestamp, or retry-count data.
- Jobs remain immutable; claims, leases, attempts, retries, and completion are
  mutable Store state. The tests verify the delivered job remains equivalent
  and hash-stable across persistence.
- The local fake adapter is in-memory and deterministic. It performs no file,
  environment, secret, logging, or network operation.
- The caller-driven one-job design has no long-running operation. Lease expiry
  in the Store provides crash recovery for a process that stops after claim.

## Traceability

The verified local transition is:

```text
same immutable job
    -> same deterministic fake adapter
    -> same DeliveryResult
    -> same persisted state transition
```

This is a local persistence property, not evidence of external message
delivery. Any external adapter requires a separate governance authorization
and bounded validation.
