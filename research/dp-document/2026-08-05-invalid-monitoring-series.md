# Invalid Monitoring Series — 2026-08-05

## Status

Diagnostic record. Excluded from Discovery Quality analysis.

## Scope

The intended series comprised three overlapping 24-hour runs:

- `RUN-20260805-130601-series-a-24h`;
- `RUN-20260805-140601-series-b-24h`;
- `RUN-20260805-150601-series-c-24h`.

The initial launcher did not execute the intended configured provider set. The
recorded Observations for each affected run came from Berlin only, rather than
all seventeen enabled providers. Automatic bounded stopping and automatic
summary generation also did not complete; local reports were generated later
after approximately 25 to 27 hours of process lifetime.

## Consequences

- `RUN-20260805-130601-series-a-24h` is superseded by
  `RUN-20260806-160947-series-a-retry-24h`.
- The three affected runs are retained as diagnostic evidence of orchestration
  behaviour only.
- They must not contribute provider-quality metrics, time-series baselines, or
  comparative Discovery Quality analysis.
- Manual report generation for runs B and C produced the same date-and-duration
  filename, so the later generation overwrote the earlier local report. This
  exposed a traceability defect in the generated filename scheme.

## Corrective Action

The research-summary generator now includes `run_id` in its generated filename.
Each future report therefore remains traceable to exactly one experiment even
when multiple runs begin on the same date and have the same rounded duration.
`run_id`, the retained run manifest, and the referenced Observation set are the
primary traceability chain; a generated filename is never the experiment
identifier.

This note does not remove or rewrite historical runtime artifacts. It records
their analytical exclusion and the reason for it.
