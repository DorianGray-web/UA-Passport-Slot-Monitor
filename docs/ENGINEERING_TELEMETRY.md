# AI Engineering Telemetry

## Purpose

This local, provider-agnostic subsystem records aggregate engineering effort
and cost facts for project analysis. It is not product analytics, does not
observe end users, and has no connection to provider monitoring, Runtime Guard,
notification delivery, or trusted capability configuration.

```text
Development session or infrastructure measurement
  -> immutable local telemetry record
  -> SQLite store
  -> daily / weekly / monthly aggregate audit
  -> optional reviewed repository report
```

The SQLite database and automatically generated reports are local runtime
artifacts and are Git-ignored. A maintainer may commit a separate, reviewed
aggregate report only when it contains no secrets, prompts, completions,
browser artifacts, personal data, or raw provider data.

## Contracts and boundaries

[`engineering_telemetry`](../engineering_telemetry/) contains immutable
`EngineeringSession` and `EngineeringMetric` records. A session records the
AI provider, model, agent, skills, token totals, estimated cost, workflow
stage, duration, and outcome. A metric is generic for future local sources
such as CI duration, VPS cost, storage use, or notification volume.

The subsystem is deliberately provider-agnostic: integration code supplies
facts through the contracts; telemetry imports no AI SDK, monitor, provider,
notification, or infrastructure adapter. It performs no network requests.

SQLite structure is versioned by ordered migrations in
[`engineering_telemetry/migrations`](../engineering_telemetry/migrations/).
`001_initial` defines the current append-only records. Future additions such
as skill, subagent, context-window, cache, MCP, VPS, CI, storage, or
notification metrics require a new numbered forward-only migration; completed
migrations are retained in the local database and never rewritten.

The complete contract is documented in
[Engineering Telemetry Contracts](contracts/engineering-telemetry.md).

## Reports

The report generator calculates consumption, cost coverage, duration,
completion rate, tokens per recorded hour, distributions by provider/model/
agent/stage/outcome, and deterministic optimization prompts. It does not infer
causality or make capability decisions.

```powershell
.\.venv-2\Scripts\python.exe .\tools\generate_engineering_telemetry_report.py --period weekly
```

Use `--at` for reproducible historical periods and `--output-directory` to
write a manually reviewed report outside the ignored runtime-report directory.

## Privacy and retention

Allowed records are aggregate engineering facts only. The contracts reject
sensitive identifiers and do not define fields for prompts, completions,
cookies, CSRF, credentials, tokens, raw HTML, screenshots, browser storage,
personal identifiers, or provider observations. Local retention is controlled
by the maintainer; deletion means removing the local SQLite database, never
rewriting records in place.

## Verification

The test strategy is in
[Engineering Telemetry Test Strategy](testing/engineering-telemetry-test-strategy.md).
Architecture protection verifies that this package remains independent from
monitoring and notification runtime layers.
