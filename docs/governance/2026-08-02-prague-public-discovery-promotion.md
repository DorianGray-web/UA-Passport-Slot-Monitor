# Prague Public Discovery Profile Promotion — 2026-08-02

## Decision scope

This governance record evaluates Prague independently under
[ADR-0011](../DECISIONS.md#adr-0011-trust-model-for-evidence-collection-and-capability-governance).
It does not infer capability from another deployment and does not generalize
the reviewed contract.

## Evidence review

The retained owner-provided live review confirms:

- Prague centre `8`, service `4`;
- one allowed date, `2026-09-01`;
- four allowed time entries from `11:45:00` through `12:45:00`;
- the bounded public sequence `LANDING -> DAYS -> TIMES -> STOP`;
- no identity submission, CAPTCHA interaction, fingerprint generation, or
  booking action.

Evidence: [Prague live observation](../../research/dp-document/2026-08-02-prague-live-observation.md).

## Governance decision

**Decision:** Accepted  
**Decision authority:** Project owner  
**Decision date:** 2026-08-02

Approve `prague-v1` public discovery for centre `8`, service `4`.

## Authorized capability

The authorization is limited to passive, HTTP-first public discovery. The
runtime validates every response, fails closed on contract deviation, may use
the explicitly enabled experimental Playwright fallback after HTTP `BLOCKED`,
and stops at `TIMES`.

The decision does not authorize CAPTCHA interaction, identity submission,
fingerprint generation, booking, or any inference about another deployment.

## Validation status

Offline registry and contract tests are required with the configuration
change. Bounded runtime validation remains a separate post-promotion task and
must not be represented as already completed.
