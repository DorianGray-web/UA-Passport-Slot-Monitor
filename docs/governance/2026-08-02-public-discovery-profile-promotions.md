# Public Discovery Profile Promotions — 2026-08-02

## Decision scope

This governance review evaluates four deployments independently under
[ADR-0011](../DECISIONS.md#adr-0011-trust-model-for-evidence-collection-and-capability-governance).
It does not infer capability from runtime observations and does not generalize
the reviewed contracts to another deployment.

## Berlin

**Decision:** approve `berlin-v1` public discovery for centre `2`, service `4`.

The retained live review confirms `LANDING -> DAYS -> TIMES -> STOP`, including
both `TIMES(0) -> NO_SLOTS` and a later `TIMES(9) -> SLOTS_AVAILABLE` outcome.
Evidence: [Berlin live observation](../../research/dp-document/2026-08-01-berlin-live-observation.md).

## Cologne

**Decision:** approve `cologne-v1` public discovery for centre `3`, service `4`.

The retained live review confirms the bounded public contract and seven
allowed time entries. Evidence: [Cologne live observation](../../research/dp-document/2026-08-01-cologne-live-observation.md).

## Bratislava

**Decision:** approve `bratislava-v1` public discovery for centre `9`, service
`4`.

The retained live review confirms the bounded public contract and seven
allowed time entries. Evidence: [Bratislava live observation](../../research/dp-document/2026-08-01-bratislava-live-observation.md).

## Toronto

**Decision:** approve `toronto-v1` public discovery for centre `46`, service
`4`.

The retained live review confirms one allowed date, 11 allowed time entries,
and the bounded public contract. Evidence: [Toronto live observation](../../research/dp-document/2026-08-01-toronto-live-observation.md).

## Shared constraints

Each approval authorizes only passive public discovery. Runtime remains
HTTP-first, validates every response, fails closed on contract deviation, and
stops at `TIMES`. Experimental Playwright fallback remains opt-in. CAPTCHA,
identity submission, and booking remain outside capability scope.

Offline validation and the bounded live runtime validation were completed on
2026-08-02. Across Berlin, Cologne, Bratislava, and Toronto, confirmed browser
discovery either reached `TIMES` or stopped at a recognized earlier
`NO_SLOTS` boundary; no browser `UNKNOWN`, browser error, or navigation beyond
the public boundary was recorded. See the
[six-hour release validation](../../research/dp-document/2026-08-02-seven-centre-6h-release-validation.md).

This validation supports the approved profiles but does not merge their
evidence or generalize the contract to another deployment.
