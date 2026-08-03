# Varna Public Discovery Live Observation

**Status:** User-provided live-observation evidence  
**Observation date:** 2026-08-03  
**Deployment:** Varna, Bulgaria  
**Public page:** `https://varna.pasport.org.ua/solutions/e-queue`

## Provenance

The project owner supplied passive browser screenshots, browser developer-tool
views, a sanitized public `days` response, a sanitized public `timeSlots`
response, and the relevant frontend `getDays()` and `getTime()` call sites.
This is user-provided live evidence, not repository-derived evidence or an
independently repeatable runtime validation.

No identity data was submitted. CAPTCHA was not solved or interacted with.
No booking or reservation action was performed.

## Observed public contract

The live review confirmed:

- `ServiceCenterId = 43`;
- `ServiceId = 4`;
- one allowed public date, `2026-09-02`;
- ten allowed public time entries;
- earliest observed time `09:25:00`;
- latest observed time `16:55:00`;
- bounded public discovery through `LANDING -> DAYS -> TIMES -> STOP`;
- a terminal normalized result of `SLOTS_AVAILABLE`.

The localized labels represented per-time capacity, while the normalized
Observation field `available_time_slots_count` records ten allowed time
entries rather than the sum of displayed appointment capacity.

## Boundary evidence

The reviewed public call sites append only the service centre, service, date
where applicable, and the opaque CSRF field for `getDays()` and `getTime()`.
The separately visible booking submission includes identity, OTP, fingerprint,
and CAPTCHA concerns. It is outside the monitoring contract and was neither
invoked nor used as evidence for discovery capability.

The monitoring boundary remains:

```text
LANDING -> DAYS -> TIMES -> STOP
```

This evidence does not authorize identity verification, CAPTCHA interaction,
fingerprint generation, or booking.

## Governance status

The project owner explicitly approved adding Varna on 2026-08-03. The
deployment-specific capability decision is recorded in the corresponding
[governance review](../../docs/governance/2026-08-03-varna-public-discovery-promotion.md).
`varna-v1` declares only passive public discovery for centre `43`, service `4`,
with fail-closed runtime validation and the terminal `TIMES` boundary.

This evidence must not be generalized to unreviewed DP Document deployments.
