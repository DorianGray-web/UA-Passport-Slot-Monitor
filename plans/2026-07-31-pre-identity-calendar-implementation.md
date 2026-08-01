# Pre-identity Calendar Monitoring — Implementation Proposal

## Status

**Partially implemented and superseded in part — 2026-07-31.**

The original proposal below is retained as an implementation-planning record.
Strict days/times classifiers, guarded discovery, Observation schema v3, and a
terminal `TIMES` boundary are implemented for Madrid, Barcelona, London, and
Milan. The runtime remains HTTP-first; those confirmed research profiles may
use an explicitly enabled experimental Playwright fallback after HTTP
`BLOCKED`.

The identity-boundary classifier, sanitized identity-boundary fixtures, and
production notification behavior remain unimplemented. The original
HTTP-only constraint was superseded by ADR-0010 only for the confirmed,
opt-in research profiles.

## Objective

Complete public `days -> times` discovery while stopping before identity
verification and preserving HTTP-only runtime monitoring.

## Proposed slices

### Slice 1 — Evidence fixtures

- capture and sanitize landing, days, times, and identity-boundary examples;
- document provenance, deployment, timestamp, and capture quality;
- exclude cookies, headers, tokens, CSRF values, fingerprints, and personal
  data from committed fixtures.

### Slice 2 — Pure response classifiers

- add a provider-specific `DaysResponseClassifier`;
- add a provider-specific `TimesResponseClassifier`;
- add an identity-boundary classifier;
- return typed evidence and normalized values;
- treat unknown payloads as `UNKNOWN`, never `NO_SLOTS`.

### Slice 3 — Guarded HTTP orchestration

- wire `DPDocumentHTTPMonitorProvider` into the monitor loop;
- reuse the existing `LandingPageClassifier`, `DiscoveryEngine`, and
  `TransitionGuard`;
- call days only after positive landing/form/CSRF evidence;
- call times only for a confirmed available date;
- stop immediately on identity-boundary evidence;
- impose a per-observation request budget.

### Slice 4 — Observation contract

- decide from real fixture needs whether schema v3 is necessary;
- if necessary, add the immutable availability structure proposed in the spec;
- preserve sanitized RequestTrace and current correlation identifiers;
- keep raw payloads outside Observation.

### Slice 5 — Regression and safety verification

- cover terminal landing, blocked, empty days, dates found, empty times, times
  found, unknown payload, and identity-boundary cases;
- assert that no booking or identity endpoint is called;
- assert that no browser dependency enters MonitorProvider;
- confirm logs and JSONL remain free of CSRF, cookies, headers, bodies,
  identity data, and fingerprints.

## Non-goals

- booking;
- reservation;
- identity verification;
- OTP, BankID, or Diia integration;
- CAPTCHA solving or challenge bypass;
- fingerprint generation;
- browser automation in normal monitoring;
- notification delivery.

## Current blocker

The 2026-07-31 clean live capture reached Cloudflare `403`, not the provider
form. User-provided live observation supports the flow but does not contain
sanitized response fixtures or confirmed selectors. Production implementation
would therefore be guesswork today.
