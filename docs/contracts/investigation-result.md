# Diagnostic Backend Contract

## Purpose

`InvestigationResult` is the only result interface exposed by diagnostic
backends to the diagnostic worker. A backend may use Node.js, Python, Go, a remote
process, or another implementation, but it must return this contract.

The worker executes an immutable queued request and stores safe result
metadata. Monitors never invoke a backend directly.

## InvestigationResult

| Field | Type | Meaning |
| --- | --- | --- |
| `success` | `bool` | `true` only when the diagnostic process completed with exit code `0`. |
| `investigation_id` | `string` | Stable correlation ID for this investigation. |
| `exit_code` | `int \| null` | External process exit code, or `null` when no exit code is available. |
| `output_directory` | `path` | Backend-managed directory associated with the investigation. |
| `summary` | `string` | Short, non-sensitive outcome suitable for monitor logs. |

All fields are required. Only `exit_code` may be `null`.

## Boundary rules

- The worker may log these five fields.
- The worker and monitor must not open or interpret `output_directory`.
- The backend owns artifact creation, retention, and access controls.
- Stdout and stderr may be captured internally by an adapter but are not part
  of this contract.
- Browser profiles, cookies, local or session storage, HAR files, network
  dumps, tokens, and session data must never cross this interface.
- `summary` must not contain raw URLs, headers, request or response bodies,
  tokens, cookies, personal data, or browser-state details.
- Backend failure must be represented as `success=false`; it must not interrupt
  monitoring.

## Responsibility layers

```text
UA-Passport-Slot-Monitor
  Observation, decision, outbox, queue, and worker
                    |
                    v
Diagnostic Adapter
  External invocation and InvestigationResult normalization
                    |
                    v
Site Investigator or another diagnostic backend
  Collection, analysis, and artifact ownership
```

Replacing Site Investigator must require only a new adapter implementing this
contract. Monitoring and state-classification logic must remain unchanged.
