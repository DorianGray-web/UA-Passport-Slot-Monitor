# Warsaw Public Discovery Profile Promotion — 2026-08-04

## Decision scope

This record evaluates Warsaw independently under
[ADR-0011](../DECISIONS.md#adr-0011-trust-model-for-evidence-collection-and-capability-governance).
It is grouped operationally under the Poland Deployment Completion milestone,
but remains an independent capability decision.

## Evidence review

The retained owner-provided live review confirms centre `10`, service
`4`, one allowed date, 15 allowed time entries, and the bounded public
sequence `LANDING -> DAYS -> TIMES -> STOP`.

Evidence: [Warsaw live observation](../../research/dp-document/2026-08-04-warsaw-live-observation.md).

## Governance decision

**Decision:** Accepted
**Decision authority:** Project owner
**Decision date:** 2026-08-04

Approve `warsaw-v1` public discovery for centre `10`, service `4`.

## Authorized capability

Authorization is limited to passive HTTP-first public discovery. Runtime must
validate each response, fail closed on contract deviation, and stop at
`TIMES`. The explicitly enabled experimental Playwright fallback may run only
after HTTP `BLOCKED`.

This decision does not authorize identity submission, CAPTCHA interaction,
fingerprint generation, booking, or inference about another deployment.

## Validation status

Offline registry and contract validation accompany this promotion. Bounded
runtime validation remains a separate deployment-specific future task, even
when all four Polish profiles are exercised in one shared run.
