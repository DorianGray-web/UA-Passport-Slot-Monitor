# Playwright Execution Profile Comparison — 2026-08-07

## Status

Research hypothesis. No runtime or provider capability change.

## Observation

`RUN-20260806-160947-series-a-retry-24h` used fresh, isolated, headless
Playwright profiles. It completed normally at the orchestrator level, but its
confirmed discovery attempts commonly stopped at `LANDING` with browser
challenge classifications. For example, Valencia recorded 26 Playwright
`BLOCKED` Observations at `LANDING` and did not reach `DAYS` or `TIMES` during
that run.

Contemporaneous live review of Valencia exposed the public form and available
time entries. This does not contradict the retained Observations: the run did
not obtain a public `TIMES` response from its own execution context.

## Interpretation

The transport label `playwright` alone is insufficient to describe an
experiment. The following execution context may affect public observability:

- headed or headless browser operation;
- persistent or non-persistent context;
- existing local profile or fresh isolated profile.

This is an investigation variable, not a claim about a provider's capability,
the public protocol, or the correctness of a live-review result.

## Follow-up

Future comparable runs must retain their Playwright execution context in the
local run manifest. A controlled, local comparison of existing persistent
profiles and fresh isolated profiles may be conducted later. It must preserve
the HTTP-first policy, public discovery boundary, privacy restrictions, and
fail-closed classification.
