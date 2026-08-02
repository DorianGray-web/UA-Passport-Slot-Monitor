# Bratislava Public Discovery Live Observation

**Status:** User-provided live-observation evidence  
**Observation date:** 2026-08-01  
**Deployment:** Bratislava, Slovakia  
**Public page:** `https://bratislava.pasport.org.ua/solutions/e-queue`

## Provenance

The project owner supplied passive browser screenshots, browser developer-tool
views, the public days and times responses, and the relevant frontend
`getDays()` and `getTime()` call sites. This is user-provided live evidence,
not repository-derived evidence or an independently repeatable runtime
validation.

No identity data was submitted. CAPTCHA was not solved or interacted with.
No booking or reservation action was performed.

## Observed public contract

The live review confirmed:

- `ServiceCenterId = 9`;
- `ServiceId = 4`;
- one allowed public date, `2026-08-31`;
- seven allowed public time entries;
- earliest observed time `15:15:00`;
- latest observed time `16:45:00`;
- bounded public discovery through `DAYS -> TIMES -> STOP`;
- a terminal normalized result of `SLOTS_AVAILABLE`.

The localized response labels reported 22 free appointments across the seven
time entries. That total is research interpretation, not the Observation
field `available_time_slots_count`, which would record seven allowed entries.

## Boundary evidence

The reviewed frontend call sites append only the public service centre,
service, date where applicable, and the opaque CSRF field for `getDays()` and
`getTime()`. Phone, CAPTCHA, fingerprint, OTP, identity, and reservation data
belong to the separately observed booking submission after public discovery.

The monitoring boundary remains:

```text
LANDING -> DAYS -> TIMES -> STOP
```

This evidence does not authorize identity verification, CAPTCHA interaction,
fingerprint generation, or booking.

## Governance status

Bratislava is present in `providers.json` as a landing-only deployment. This
observation confirms the public contract but does not enable a discovery
profile. Explicit governance review, a reviewed registry change, offline
tests, and bounded runtime validation remain required before promotion.

The evidence must not be generalized to unreviewed DP Document deployments.

> **Supersession note — 2026-08-02:** Following explicit governance review,
> `bratislava-v1` is now declared in `providers.json` for centre `9`, service
> `4`. The historical evidence and pre-promotion status above remain intact;
> the decision is recorded in the separate governance history.
