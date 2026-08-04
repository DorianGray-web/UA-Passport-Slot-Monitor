# Engineering Telemetry Contracts

All telemetry records are immutable, versioned local facts.

| Contract | Responsibility |
|---|---|
| `EngineeringSession` | Aggregate AI-assisted development session facts. |
| `EngineeringMetric` | Generic quantitative measurement for a future source. |

`EngineeringSession` fields: session ID, UTC timestamp, provider, model,
agent, immutable skill tuple, workflow stage, duration, outcome, optional
input/output/cached token counts, and optional estimated USD cost.

`EngineeringMetric` fields: metric ID, UTC timestamp, source, metric name,
numeric value, unit, and optional session ID.

Neither contract permits prompts, completions, credentials, raw site data,
browser/session artifacts, recipient data, or runtime observations. Unknown
schema versions fail closed.

The SQLite schema has independent forward-only migrations. Contract schema
versions describe record meaning; a migration is required only when persisted
storage changes. Adding an aggregate field or a future metric source must not
rewrite existing local facts.
