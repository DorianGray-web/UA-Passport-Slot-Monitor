# Warsaw Public Discovery Live Observation

**Status:** User-provided live-observation evidence
**Observation date:** 2026-08-04
**Deployment:** Warsaw, Poland
**Public page:** `https://warszawa.pasport.org.ua/solutions/e-queue`

## Provenance

The project owner supplied passive browser screenshots, developer-tool views,
a sanitized public `timeSlots` response, and the relevant frontend public
discovery call sites. This is user-provided live evidence, not independently
repeatable runtime validation.

No identity data was submitted. CAPTCHA was not solved or interacted with. No
booking or reservation action was performed.

## Observed public contract

- `ServiceCenterId = 10`;
- `ServiceId = 4`;
- one allowed date, `2026-08-19`;
- 15 allowed public time entries;
- earliest observed time `12:45:00`;
- latest observed time `16:15:00`;
- bounded public discovery through `LANDING -> DAYS -> TIMES -> STOP`;
- terminal normalized result `SLOTS_AVAILABLE`.

The localized slot labels describe capacity per time entry. The normalized
`available_time_slots_count` records 15 allowed time entries rather than
the sum of displayed appointment capacity.

## Boundary and interpretation

The reviewed `getDays()` and `getTime()` call sites belong to the public
pre-identity workflow. Separately visible phone, OTP, fingerprint, CAPTCHA,
identity, and booking operations are outside the monitoring contract and were
not invoked or used as discovery evidence.

This observation independently confirms Warsaw; it does not infer a rule for
future Polish deployments. Additional deployments require independent evidence
and governance review.

## Governance status

The project owner approved the deployment-specific capability on 2026-08-04.
The corresponding governance decision authorizes only passive, fail-closed,
HTTP-first public discovery with an optional explicitly enabled experimental
Playwright fallback after HTTP `BLOCKED`, ending at `TIMES`.
