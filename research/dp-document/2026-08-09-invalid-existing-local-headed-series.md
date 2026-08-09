# Invalid Existing-Local Headed Monitoring Series — 2026-08-09

## Status

`INVALID` for availability and comparative Discovery Quality analysis.

Retained as transport-health and research-runtime diagnostic evidence.

## Scope

- Run ID: `RUN-20260809-101949-existing-local-headed-24h`
- Observation coverage: 2026-08-09 10:20:42–18:38:10 Europe/Amsterdam
- Coverage duration: 8h 17m
- Configured cohort: seventeen DP Document deployments
- Browser context: headed Playwright with existing local persistent profiles
- Stop reason: manually cancelled after the run was determined to be
  analytically invalid

The process tree required forced termination after the initial termination
signal did not close all supervised Python and Chromium children. Immutable
Observations and local runtime artifacts were retained.

## Aggregate Statistics

| Metric | Value |
|---|---:|
| Total Observations | 199 |
| HTTP landing attempts | 199 |
| HTTP landing `200` | 15 |
| HTTP landing `403` | 155 |
| HTTP landing `429` | 29 |
| HTTP-blocked cycles | 184 |
| Playwright runs | 192 |
| Playwright runs reaching `LANDING` | 192 |
| Playwright runs reaching `DAYS` | 0 |
| Playwright runs reaching `TIMES` | 0 |
| Availability classifications at `TIMES` | 0 |
| Mean Playwright duration | 6.25 s |

Seven cycles produced a recognized landing-level `NO_SLOTS` result over HTTP.
They remain immutable Observations, but they do not make this systematically
obstructed run a comparable availability experiment.

## Observed Problem

The intended experiment was provider availability monitoring. Instead, the
run measured a cohort-wide automated-browser obstruction:

```text
HTTP LANDING -> BLOCKED
Playwright LANDING -> Cloudflare challenge
STOP as BLOCKED
```

No Playwright execution reached the public `DAYS` or `TIMES` stages. Therefore
zero successful availability classifications means that no valid calendar
sample was obtained; it does not mean that no appointments existed.

Contemporaneous manual live reviews for Madrid, London, and Valencia reached
the unchanged public `LANDING -> DAYS -> TIMES -> STOP` boundary and returned
non-empty public time-slot responses. These reviews contained no booking
action and are retained here only as a sanitized comparative conclusion. Raw
browser captures, session state, request details, and personal data are not
part of this note.

## Cross-Run Context

The preceding all-provider series on 2026-08-05 initially completed public
discovery, then degraded across the cohort. Thirteen deployments first
recorded browser `BLOCKED` outcomes within the shared interval
09:28–09:35 UTC. The same series recorded 967 Playwright attempts over twelve
hours with a median cross-provider gap of 31.1 seconds.

The successful seven-centre six-hour release validation had recorded 202
Playwright executions, 117 `TIMES` completions, 85 recognized earlier
`NO_SLOTS` outcomes, and no browser `UNKNOWN` or browser error. Expanding the
same independent 7–12 minute provider schedule to seventeen processes changed
the aggregate browser-attempt cadence without introducing a cohort-wide rate
budget or circuit breaker.

## Interpretation

The evidence confirms an execution-context and experiment-design failure, not
a provider-contract failure. The strongest current explanation is that
per-provider scheduling was scaled to a seventeen-provider cohort without a
global Playwright rate budget or a cohort-level circuit breaker. Per-provider
cooldown reduced each individual process but continued automated browser
attempts across the cohort. The later FIFO lease serialized contexts but did
not provide global pacing or stop the experiment after synchronized challenge
evidence.

This explanation remains an evidence-backed working interpretation rather
than proof of a specific provider-side rate-limit rule. Worker, notification,
and Engineering Telemetry components do not participate in the discovery
path. The public discovery contract remained independently observable in live
review.

## Analytical Treatment

- Retain the run in research history with status `INVALID`.
- Include its aggregate counts only in transport-health and invalid-run
  statistics.
- Exclude it from availability rates, provider-quality comparisons,
  discovery-completion baselines, moving averages, and drift conclusions.
- Do not interpret `BLOCKED` as `NO_SLOTS` or as evidence of provider
  unavailability.
- Do not use this run to revise or demote governed provider capabilities.

## Corrective Direction

Before another comparable multi-provider run, require a clean research
readiness result and explicit browser execution conditions. Future runtime
design should separately evaluate a cohort-wide Playwright rate budget and a
human-governed circuit breaker for synchronized `BLOCKED @ LANDING` evidence.
Those changes require their own design and validation; this diagnostic record
does not authorize an automatic runtime or capability change.

This note does not remove or rewrite historical Observations. It records their
analytical status, the reason for exclusion, and the limited diagnostic use
that remains valid.
