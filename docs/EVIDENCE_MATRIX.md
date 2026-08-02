# Evidence Matrix

## Purpose

This document is the current operational map of provider trust. It shows where
each configured deployment, and each evidence-confirmed candidate deployment,
is in the evidence-to-capability lifecycle defined by
[ADR-0011](DECISIONS.md#adr-0011-trust-model-for-evidence-collection-and-capability-governance).

ADR-0011 defines **how trust works**. This matrix records the **current trust
state**.

The matrix is documentation, not executable configuration. `providers.json`
remains the declarative source of truth for runtime capabilities. A matrix
change cannot enable, revise, or remove a provider capability.

## Lifecycle

```text
Reality
  -> Observation
  -> Evidence
  -> Governance Review
  -> Capability
  -> Runtime
  -> Observation
```

The cycle is self-updating because runtime produces new observations. It is
not self-modifying: observations and evidence never change trusted runtime
capabilities automatically.

## Summary

| Measure | Count |
|---|---:|
| Deployments tracked by this matrix | 11 |
| Deployments configured in `providers.json` | 11 |
| Evidence-confirmed public contracts | 9 |
| Approved runtime discovery profiles | 9 |
| Governance-pending discovery candidates | 0 |
| Unconfirmed landing-only research deployments | 2 |
| Discovery profiles completing bounded release validation | 9 |

Berlin, Toronto, Cologne, and Bratislava were approved independently on
2026-08-02. The two unconfirmed landing-only research deployments are Kortrijk
and Chisinau.

## Current deployment state

| Deployment | Observation | Public contract | Comparative validation | Governance | Runtime |
|---|---|---|---|---|---|
| Madrid | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Barcelona | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| London | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Milan | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Valencia | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Berlin | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Toronto | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Cologne | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Bratislava | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Kortrijk | Landing only | Unconfirmed | Not eligible | Not eligible | `landing-only` |
| Chisinau | Landing only | Unconfirmed | Not eligible | Not eligible | `landing-only` |

`Confirmed` means the retained evidence is sufficient for that column. It does
not imply registry enablement. `Pending` means the evidence supports a
governance review, but no capability decision has been recorded in
`providers.json`. `Not eligible` means an earlier lifecycle requirement is not
yet satisfied.

## Current comparative finding

Nine deployments currently have reviewed public discovery evidence:
Madrid, Barcelona, London, Milan, Valencia, Berlin, Toronto, Cologne, and
Bratislava. Each reached the bounded high-level sequence:

```text
LANDING -> DAYS -> TIMES -> STOP
```

Berlin is the reference case for outcome variability within one confirmed
contract. The same allowed date first produced `TIMES(0) -> NO_SLOTS` and
later `TIMES(9) -> SLOTS_AVAILABLE`. The stage sequence remained unchanged;
the recognized `timeSlots` content determined the normalized result.

This finding is limited to the reviewed deployments and observation windows.
It is not a protocol guarantee for unconfirmed or future deployments.

The 2026-08-02 six-hour release validation exercised Berlin, Cologne,
Bratislava, and Toronto alongside Madrid and Barcelona controls. Cologne was
`NO_SLOTS` throughout that window despite its earlier live availability
evidence. Kortrijk's candidate probe found no queue form or identifiers and
did not change its landing-only trust state.

## Capability Promotion Checklist

- [ ] Live observation recorded
- [ ] Research note sanitized
- [ ] Evidence provenance documented
- [ ] Public contract confirmed
- [ ] Comparative validation completed
- [ ] ADR-0011 constraints satisfied
- [ ] Explicit governance review recorded
- [ ] `providers.json` updated
- [ ] Runtime guard and tests passed
- [ ] Bounded runtime validation completed or explicitly scheduled
- [ ] Evidence Matrix updated
- [ ] CHANGELOG updated

Completing research items does not authorize the configuration change. The
capability becomes trusted only after explicit governance approval and a
reviewed `providers.json` change.

## Capability Revision or Removal

Runtime refusal is immediate and execution-scoped; governance change is
explicit and persistent. An unexpected response may cause `UNKNOWN` or
`BLOCKED` without editing this matrix or demoting a profile automatically.

A capability revision or removal requires:

- retained contradictory or superseding evidence;
- an explicit governance decision;
- a reviewed `providers.json` change;
- corresponding tests and documentation updates.

## Evidence references

- [Cross-deployment comparison](../research/dp-document/2026-08-01-cross-deployment-public-discovery-comparison.md)
- [2026-08-02 governance review](governance/2026-08-02-public-discovery-profile-promotions.md)
- [Seven-centre six-hour release validation](../research/dp-document/2026-08-02-seven-centre-6h-release-validation.md)
- [Berlin live observation](../research/dp-document/2026-08-01-berlin-live-observation.md)
- [Toronto live observation](../research/dp-document/2026-08-01-toronto-live-observation.md)
- [Cologne live observation](../research/dp-document/2026-08-01-cologne-live-observation.md)
- [Bratislava live observation](../research/dp-document/2026-08-01-bratislava-live-observation.md)
- [Valencia live observation](../research/dp-document/2026-08-01-valencia-live-observation.md)
- [Barcelona live observation](../research/dp-document/2026-07-31-barcelona-live-observation.md)
- [Bratislava and Milan live observation](../research/dp-document/2026-07-30-bratislava-milan-live-observation.md)
- [Kortrijk technical spike](../research/dp-document/belgium-kortrijk-spike.md)
