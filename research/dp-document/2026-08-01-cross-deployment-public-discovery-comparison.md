# Cross-Deployment Public Discovery Comparison

**Evidence date:** 2026-08-01  
**Status:** reviewed comparative research observation

## Scope

This note compares the currently evidence-confirmed DP Document deployments.
It summarizes retained owner-provided live observations and bounded runtime
evidence. It does not claim a universal provider protocol or infer behaviour
for unreviewed deployments.

## Confirmed deployments

| Deployment | ServiceCenterId | ServiceId | Observed public outcome |
|---|---:|---:|---|
| Madrid | 6 | 4 | `SLOTS_AVAILABLE` |
| Barcelona | 41 | 4 | `SLOTS_AVAILABLE` |
| London | 47 | 4 | `SLOTS_AVAILABLE` |
| Milan | 4 | 4 | `SLOTS_AVAILABLE` |
| Valencia | 7 | 4 | `SLOTS_AVAILABLE` |
| Berlin | 2 | 4 | `NO_SLOTS`, later `SLOTS_AVAILABLE` for the same allowed date |
| Toronto | 46 | 4 | `SLOTS_AVAILABLE` |
| Cologne | 3 | 4 | `SLOTS_AVAILABLE` |
| Bratislava | 9 | 4 | `SLOTS_AVAILABLE` |

All nine reviewed deployments exposed the same high-level bounded public
workflow:

```text
LANDING -> DAYS -> TIMES -> STOP
```

Berlin is the reference example for outcome variability within that contract:

```text
Earlier: DAYS (1) -> TIMES (0) -> NO_SLOTS -> STOP
Later:   DAYS (1) -> TIMES (9) -> SLOTS_AVAILABLE -> STOP
```

The transition boundary did not change. The observed availability result was
determined by the confirmed contents of `timeSlots`.

## Evidence classification

**Observed evidence:** all nine deployments reached `DAYS` and `TIMES` using
service `4`; the retained responses produced the outcomes in the table.

**Confirmed capability:** each listed deployment has a reviewed public
discovery contract through `TIMES -> STOP`. Registry enablement remains a
separate governance-controlled capability.

**Interpretation:** within this evidence set, differences between centres and
observation times appeared in the returned public availability data rather
than in the high-level discovery-stage sequence. Berlin directly demonstrates
both terminal availability outcomes within one deployment.

**Generalization:** none beyond these nine deployments and their reviewed
observation windows. The evidence does not establish identical CSRF fields,
`check_services` requirements, response extensions, availability policies, or
future behaviour. It does not establish the contract for Kortrijk, Chisinau,
or any future deployment.

## Monitoring implication

`NO_SLOTS` must retain its discovery-stage context:

- landing-level `NO_SLOTS` is supported by a confirmed landing marker;
- post-discovery `NO_SLOTS` is supported by a recognized `TIMES` response with
  no allowed time entries;
- `SLOTS_AVAILABLE` is supported by a recognized `TIMES` response with one or
  more allowed entries.

The state is derived from evidence, not from a deployment-specific branch or
an assumed centre reputation.

> **Supersession note — 2026-08-02:** A later owner-provided Prague review
> independently confirmed centre `8`, service `4`, one allowed date, four
> allowed time entries, and the same bounded `LANDING -> DAYS -> TIMES -> STOP`
> sequence. Prague is documented separately rather than rewriting this
> historical nine-deployment comparison.
