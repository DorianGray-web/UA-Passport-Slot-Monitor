# Kortrijk Candidate Form Observation

**Status:** Candidate evidence only  
**Observed:** 2026-08-02 10:30 Europe/Amsterdam  
**Source:** bounded local runtime probe  
**Deployment:** Kortrijk

## Observed facts

The opt-in candidate probe reached an HTTP `200` public queue form and recorded
only sanitized structural evidence:

- `ServiceCenterId=48`;
- one visible service option with `ServiceId=4` and the public passport/ID-card
  label;
- service, date, and time selectors were present;
- discovery stopped at `LANDING`.

The probe did not select the service, request `DAYS`, request `TIMES`, submit
identity information, interact with CAPTCHA, or perform booking.

## Interpretation

This observation increases the candidate evidence corpus. It does not confirm
that the visible option is the governed target service, the request/response
schemas, date-dependent time discovery, or the complete bounded public
contract.

Kortrijk therefore remains a landing-only research deployment. Promotion to a
discovery profile requires explicit governance review after independently
confirmed `LANDING -> DAYS -> TIMES -> STOP` evidence.

## Repository boundary

The local candidate artifact remains Git-ignored. This note contains no CSRF
value, cookies, headers, browser storage, raw HTML, screenshots, HAR, personal
data, or booking data.
