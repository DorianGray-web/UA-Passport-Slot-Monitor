# Seven-centre Candidate Evidence Comparison

> **Supersession note — 2026-08-01:** During this run, owner-provided live
> browser evidence confirmed Berlin centre `2`, service `4`, and the complete
> public `LANDING -> DAYS -> TIMES -> STOP` contract. Berlin is therefore no
> longer landing-only in the evidence corpus. This historical plan remains an
> accurate record of the knowledge state at launch. Kortrijk remains
> landing-only and candidate-only. No runtime registry capability was changed
> by this documentation update.

**Status:** Historical; completed and superseded — 2026-08-02  
**Date:** 2026-08-01

> **Completion note — 2026-08-02:** The historical comparison completed.
> Berlin was independently confirmed and later promoted through governance.
> Kortrijk was migrated to the shared `CityMonitor`; its later six-hour
> release-validation candidate probe found no queue form, service selector,
> options, or identifiers. Kortrijk remains landing-only. See the
> [six-hour release validation](2026-08-02-seven-centre-6h-release-validation.md).

## Goal

Compare five evidence-confirmed public-discovery profiles with two
landing-only centres whose service identifiers remain unconfirmed.

## Cohort

Confirmed discovery group:

- Madrid;
- Barcelona;
- London;
- Milan;
- Valencia.

Candidate landing group:

- Berlin;
- Kortrijk.

## Runtime boundaries

All centres remain HTTP-first. The five confirmed profiles may use the
explicitly enabled experimental Playwright fallback and stop at `TIMES`.

Berlin and Kortrijk remain without `public_discovery_profile`. Their optional
candidate probe may run only after HTTP `BLOCKED`, only for a new
`(provider_id, transport, page_hash)` key, and under a six-hour default
cooldown. It may inspect the public landing form but must not select a service,
request days or times, interact with CAPTCHA, enter identity data, or perform
booking.

## Local outputs

Standard Observations remain unchanged. Sanitized candidate material may be
written locally to:

```text
research-output/candidate-evidence/berlin/candidate-services.json
research-output/candidate-evidence/kortrijk/candidate-services.json
```

These paths are Git ignored. They contain no CSRF values, cookies, headers,
HTML, screenshots, browser storage, CAPTCHA data, fingerprints, or personal
information. Candidate evidence cannot modify `providers.json`.

## Analysis questions

- How often does HTTP return `200`, `403`, `NO_SLOTS`, or `UNKNOWN` for each
  group?
- Do Berlin or Kortrijk expose `QUEUE_FORM_FOUND` during the same periods as
  confirmed centres expose dates and times?
- Does a changed blocked-page hash correspond to a materially different
  browser landing result?
- Are cross-centre landing changes synchronized?
- Does either candidate centre expose stable public centre and service option
  values suitable for governance review?

## Completion

Stop the orchestrator manually after three to four hours. The generated report
must distinguish confirmed discovery fallbacks from candidate landing probes.
Any candidate artifact requires separate governance review and documented
confirmation before a discovery profile may be added.
