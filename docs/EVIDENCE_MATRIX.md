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
| Deployments tracked by this matrix | 17 |
| Deployments configured in `providers.json` | 17 |
| Evidence-confirmed public contracts | 17 |
| Approved runtime discovery profiles | 17 |
| Governance-pending discovery candidates | 0 |
| Unconfirmed landing-only research deployments | 0 |
| Discovery profiles completing bounded release validation | 9 |

Berlin, Toronto, Cologne, and Bratislava were approved independently on
2026-08-02. Kortrijk was independently approved on 2026-08-04 after a live
review confirmed its bounded public discovery contract. Prague was independently approved on 2026-08-02; its bounded
post-promotion runtime validation remains scheduled rather than completed.
Varna was independently approved on 2026-08-03; its bounded post-promotion
runtime validation is also pending.
Chisinau was independently approved on 2026-08-03; its bounded post-promotion
runtime validation is pending.
Warsaw, Krakow, Gdansk, and Wroclaw were approved independently on 2026-08-04
under the Poland Deployment Completion milestone. Their deployment-specific
bounded runtime validation remains pending.

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
| Prague | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Varna | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Kortrijk | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Chisinau | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Warsaw | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Krakow | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Gdansk | Confirmed | Confirmed | Confirmed | Approved | `discovery` |
| Wroclaw | Confirmed | Confirmed | Confirmed | Approved | `discovery` |

`Confirmed` means the retained evidence is sufficient for that column. It does
not imply registry enablement. `Pending` means the evidence supports a
governance review, but no capability decision has been recorded in
`providers.json`. `Not eligible` means an earlier lifecycle requirement is not
yet satisfied.

## Current comparative finding

Seventeen deployments currently have reviewed public discovery evidence:
Madrid, Barcelona, London, Milan, Valencia, Berlin, Toronto, Cologne, and
Bratislava, Prague, Varna, Chisinau, Kortrijk, Warsaw, Krakow, Gdansk, and Wroclaw.
Each reached the bounded high-level sequence:

```text
LANDING -> DAYS -> TIMES -> STOP
```

Berlin is the reference case for outcome variability within one confirmed
contract. The same allowed date first produced `TIMES(0) -> NO_SLOTS` and
later `TIMES(9) -> SLOTS_AVAILABLE`. The stage sequence remained unchanged;
the recognized `timeSlots` content determined the normalized result.

This finding is limited to the reviewed deployments and observation windows.
It is not a protocol guarantee for unconfirmed or future deployments.

Across the four currently evidence-confirmed Polish deployments, the same
bounded public discovery contract was observed with `ServiceId=4`, sequential
`ServiceCenterId` values `10` through `13`, and the common terminal boundary.
No general rule is inferred for future Polish deployments. Additional
deployments require independent evidence and governance review.

The 2026-08-02 six-hour release validation exercised Berlin, Cologne,
Bratislava, and Toronto alongside Madrid and Barcelona controls. Cologne was
`NO_SLOTS` throughout that window despite its earlier live availability
evidence. Kortrijk's probe in that historical window found no queue form or
identifiers. The historical candidate probe remains retained as evidence of
the state at that time. A later 2026-08-04 live review independently confirmed
centre `48`, service `4`, one allowed date, seven allowed time entries, and
the bounded sequence `LANDING -> DAYS -> TIMES -> STOP`; explicit governance
then approved `kortrijk-v1`.

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
- [Prague governance review](governance/2026-08-02-prague-public-discovery-promotion.md)
- [Prague live observation](../research/dp-document/2026-08-02-prague-live-observation.md)
- [Varna governance review](governance/2026-08-03-varna-public-discovery-promotion.md)
- [Varna live observation](../research/dp-document/2026-08-03-varna-live-observation.md)
- [Chisinau live observation](../research/dp-document/2026-08-03-chisinau-live-observation.md)
- [Warsaw governance review](governance/2026-08-04-warsaw-public-discovery-promotion.md)
- [Warsaw live observation](../research/dp-document/2026-08-04-warsaw-live-observation.md)
- [Krakow governance review](governance/2026-08-04-krakow-public-discovery-promotion.md)
- [Krakow live observation](../research/dp-document/2026-08-04-krakow-live-observation.md)
- [Gdansk governance review](governance/2026-08-04-gdansk-public-discovery-promotion.md)
- [Gdansk live observation](../research/dp-document/2026-08-04-gdansk-live-observation.md)
- [Wroclaw governance review](governance/2026-08-04-wroclaw-public-discovery-promotion.md)
- [Wroclaw live observation](../research/dp-document/2026-08-04-wroclaw-live-observation.md)
- [Kortrijk governance review](governance/2026-08-04-kortrijk-public-discovery-promotion.md)
- [Kortrijk live observation](../research/dp-document/2026-08-04-kortrijk-live-observation.md)
- [Seven-centre six-hour release validation](../research/dp-document/2026-08-02-seven-centre-6h-release-validation.md)
- [Berlin live observation](../research/dp-document/2026-08-01-berlin-live-observation.md)
- [Toronto live observation](../research/dp-document/2026-08-01-toronto-live-observation.md)
- [Cologne live observation](../research/dp-document/2026-08-01-cologne-live-observation.md)
- [Bratislava live observation](../research/dp-document/2026-08-01-bratislava-live-observation.md)
- [Valencia live observation](../research/dp-document/2026-08-01-valencia-live-observation.md)
- [Barcelona live observation](../research/dp-document/2026-07-31-barcelona-live-observation.md)
- [Bratislava and Milan live observation](../research/dp-document/2026-07-30-bratislava-milan-live-observation.md)
- [Kortrijk candidate form observation](../research/dp-document/2026-08-02-kortrijk-candidate-form-observation.md)
- [Kortrijk technical spike](../research/dp-document/belgium-kortrijk-spike.md)
