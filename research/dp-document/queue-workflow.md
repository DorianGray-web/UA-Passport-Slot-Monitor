# DP Document Queue Workflow Research

**Location under study:** Kortrijk, Belgium

**Status:** Provider feasibility research

**Last updated:** 2026-07-21

## Purpose

This study evaluates whether appointment availability can be monitored responsibly without automatic booking, CAPTCHA bypass, or collection of passport details.

## Confirmed observations

- A standard direct HTTP request may receive `403 Forbidden`.
- Frontend 7.34.2 exposes pre-authentication HTTP queue discovery through
  `form=days` and `form=times`.
- Queue discovery requires service centre, service, CSRF, and date for times;
  it does not require a browser fingerprint.
- The publicly delivered client application exposes the general appointment workflow.
- The observed workflow contains separate stages for service selection, available days, available times, and manual registration.
- Access restrictions, CAPTCHA pages, incomplete captures, and application errors require states distinct from `NO_SLOTS`.

## Generalized workflow

```mermaid
flowchart TD
    S["Select service"] --> D["Check available days"]
    D --> T["Check available times"]
    T --> R["Manual registration"]
```

## In progress

- capturing a valid live response for available days;
- capturing a valid live response for time slots;
- validating centre-specific HTTP session, CSRF, and response schemas;
- defining a normalized provider response;
- determining responsible polling, backoff, and pause behavior.

## Not yet implemented

- a production provider adapter;
- persistent session management;
- automated availability-change detection;
- user challenge-intervention flow;
- notification delivery based on real provider changes.

## Safety boundary

This public note excludes secrets, session values, generated fingerprints,
CAPTCHA tokens, raw captures, and booking-reproduction instructions. The
minimal public monitoring contract is documented because it contains no
authentication, personal data, or fingerprint parameter.

The research describes what has been established, not a recipe for interacting with undocumented provider internals.
