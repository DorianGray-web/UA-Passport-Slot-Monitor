# Cologne Public Discovery Live Observation

**Status:** User-provided live-observation evidence  
**Observation date:** 2026-08-01  
**Deployment:** Cologne, Germany  
**Public page:** `https://cologne.pasport.org.ua/solutions/e-queue`

## Provenance

The project owner supplied passive browser screenshots, browser developer-tool
views, a sanitized public `timeSlots` response, and the relevant frontend
`getDays()` and `getTime()` call sites. Screenshot filenames place part of the
review at approximately 22:10 Europe/Amsterdam. This is user-provided live
evidence, not repository-derived evidence or an independently repeatable
runtime validation.

No identity data was submitted. CAPTCHA was not solved or interacted with.
No booking or reservation action was performed.

## Observed public contract

The live review confirmed:

- `ServiceCenterId = 3`;
- `ServiceId = 4`;
- one allowed public date, `2026-08-31`;
- seven allowed public time entries;
- earliest observed time `15:20:00`;
- latest observed time `17:20:00`;
- bounded public discovery through `DAYS -> TIMES -> STOP`;
- a terminal normalized result of `SLOTS_AVAILABLE`.

The seven localized labels each reported 15 free appointments. Their displayed
capacity therefore summed to 105 appointments during this observation. That
sum is research interpretation, not the Observation field
`available_time_slots_count`, which would record seven allowed time entries.

## Boundary evidence

The reviewed frontend call sites append only the public service centre,
service, date where applicable, and the opaque CSRF field for `getDays()` and
`getTime()`. The separately reviewed booking submission appends phone,
CAPTCHA, fingerprint, OTP, and reservation-related data only after public
discovery.

The monitoring boundary remains:

```text
LANDING -> DAYS -> TIMES -> STOP
```

This evidence does not authorize identity verification, CAPTCHA interaction,
fingerprint generation, or booking.

## Governance status

Cologne is not present in `providers.json`. This observation increases the
evidence corpus but does not create a runtime capability. Comparative
validation, explicit governance review, registry configuration, offline tests,
and bounded runtime validation remain separate requirements.

The evidence must not be generalized to unreviewed DP Document deployments.

> **Supersession note — 2026-08-02:** `cologne-v1` was approved independently
> and added to `providers.json` for centre `3`, service `4`. The original
> pre-promotion status above remains part of the evidence history.
