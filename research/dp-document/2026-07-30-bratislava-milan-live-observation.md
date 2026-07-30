# Bratislava and Milan Live Observation — 2026-07-30

## Evidence classification

- **Source:** User-provided passive browser observation
- **Observation date:** 2026-07-30
- **Confirmed session window:** 18:28:10–19:50:23 Europe/Amsterdam
  (UTC+02:00)
- **Timestamp source:** Screenshot filenames
- **Observed deployments:** Bratislava and Milan
- **Reproducibility status:** Not independently repeated by the project

This evidence was collected by the project owner and cannot be derived from
repository code, tests, fixtures, or documentation. It must not be presented as
automated monitor validation.

The available folder overview establishes the overall session window. It does
not establish an exact start or end time for either centre. Per-centre
timestamps must not be assigned unless individual screenshots or filenames
provide sufficient evidence.

## Reported observations

The captured research sequence included direct interaction with the provider
pages followed by inspection of requests and responses in browser developer
tools.

The project owner observed that:

- available dates and available times were retrieved in separate request
  steps;
- time discovery depended on a previously selected date;
- comparable high-level `dates -> times` behavior appeared in both Bratislava
  and Milan.

These observations support keeping date discovery and time discovery as
separate operations in the HTTP-first provider contract.

## Limits of the evidence

This observation does not establish that Bratislava and Milan share:

- identical endpoints or form names;
- field names or request parameters;
- CSRF acquisition or validation behavior;
- response schemas;
- session requirements;
- availability semantics.

It also does not confirm that the repository's current monitor loops perform
the observed sequence. The loops still classify landing responses only, and
the HTTP `days`/`times` adapter requires deployment-specific live validation
before its responses can be normalized safely.

