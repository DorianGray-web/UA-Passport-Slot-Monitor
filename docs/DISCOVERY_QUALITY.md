# Discovery Quality

> **Status:** Normative analytical specification. Offline aggregation is not
> implemented.

## 1. Purpose (Normative)

Discovery Quality defines an offline analytical layer for evaluating provider
discovery behaviour across completed experiments. It does not participate in
runtime execution, capability governance, notification delivery, or provider
configuration.

## 2. Core Principle (Normative)

> **All observability layers consume evidence. None is a source of runtime
> control or capability change.**

Discovery Quality exists solely to improve human understanding of provider
discovery behaviour over time.

## 3. Scope (Normative)

Discovery Quality may use:

- completed experiments;
- immutable Observations;
- completed Research Summaries;
- local offline analytical reports.

It must not use or modify runtime execution, schedulers, provider profiles,
`providers.json`, notification pipelines, governance state, or Engineering
Telemetry sessions.

## 4. Normative Invariants (Normative)

### DQ-001 — Read-only

Discovery Quality shall never modify `providers.json`, the capability registry,
runtime configuration, notification policies, or transport selection.

### DQ-002 — Traceable Metrics

Discovery Quality metrics shall be traceable to immutable Observations.
Research Summaries may determine run boundaries, experiment metadata, and
analytical context, but every reported metric shall remain reproducible from
the referenced Observation set.

### DQ-003 — Analytical Signals

`UNKNOWN` and `BLOCKED` are analytical signals. They shall never trigger an
automatic runtime change, classifier relaxation, or capability decision.

### DQ-004 — Investigation, Not Capability Change

Drift creates Investigation Candidates for human review. Drift never creates a
capability promotion, demotion, registry change, or transport-policy change.

### DQ-005 — Local Reports

Automatically generated Discovery Quality reports remain local runtime output.
Only manually reviewed and sanitized aggregate conclusions may enter the
repository.

## 5. Primary Evidence (Normative)

Immutable Observations are the authoritative source of quantitative discovery
data. They provide the state, transport, discovery stage, timing, and
availability counts used by the analysis.

Completed Research Summaries provide run boundaries, configuration metadata,
experiment context, and human-readable interpretation. They are contextual
artifacts, not an independent source of quantitative truth.

## 6. Derived Metrics (Normative)

Derived metrics describe a referenced provider and completed run or explicit
series of completed runs. A zero denominator yields an undefined metric, not
zero percent.

### Discovery Completion

```text
(SLOTS_AVAILABLE + NO_SLOTS) / Playwright Discovery Runs
```

This measures deterministic completion of bounded public discovery, not the
presence of available appointments.

Other valid derived metrics include:

- `UNKNOWN` ratio;
- HTTP `BLOCKED` ratio;
- average discovery duration;
- `TIMES` completion ratio;
- counts of `SLOTS_AVAILABLE` and `NO_SLOTS`.

Derived metrics shall never become runtime inputs.

## 7. Time-Series Model (Normative)

Discovery Quality retains provider-specific, run-level values. Moving averages,
rolling trends, and drift indicators are derived views over that history; they
must retain references to the completed runs and Observation sets from which
they were calculated.

No aggregate may conceal the availability of its underlying run-level values.

## 8. Architecture (Informative)

```text
Immutable Observations
        │
        ▼
Completed Research Summary
        │
        ▼
Offline Discovery Quality Aggregator
        │
        ▼
Local Discovery Quality Report
        │
        ▼
Human Investigation
```

There is no return path from this analytical flow to runtime.

## 9. Relationship to Other Observability Layers (Informative)

| Layer | Primary question |
|---|---|
| Engineering Telemetry | How efficiently is the project developed? |
| Discovery Quality | How stable is bounded provider discovery over time? |
| Verification Reports | What happened in a particular experiment or review? |

Engineering Telemetry measures development cost and efficiency. Discovery
Quality measures discovery behaviour. Verification Reports retain
experiment-specific evidence. The systems are intentionally independent;
combined reports may be generated only without runtime coupling.

## 10. Future Offline Aggregator (Informative)

Implementation is deferred until the project has accumulated a sufficiently
comparable series of completed long-running experiments. Future work may add:

- an offline aggregator;
- local report generation;
- provider-specific historical trend analysis;
- optional combined engineering reports.

These future capabilities require separate design, implementation, and
validation. They do not authorize runtime changes.
