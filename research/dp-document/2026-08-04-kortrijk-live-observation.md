# Kortrijk Public Discovery Live Observation

**Status:** User-provided live-observation evidence
**Observation date:** 2026-08-04
**Deployment:** Kortrijk, Belgium
**Public page:** `https://kortrijk.pasport.org.ua/solutions/e-queue`

## Provenance

The project owner supplied passive browser screenshots, developer-tool views,
sanitized public `DAYS` and `TIMES` responses, and relevant frontend public
discovery call sites. This is user-provided live evidence, not independently
repeatable runtime validation.

No identity data was submitted. CAPTCHA was not solved or interacted with. No
booking or reservation action was performed.

## Observed public contract

- `ServiceCenterId = 48`;
- `ServiceId = 4`;
- one allowed date, `2026-08-19`;
- seven allowed public time entries;
- earliest observed time `09:40:00`;
- latest observed time `16:20:00`;
- bounded public discovery through `LANDING -> DAYS -> TIMES -> STOP`;
- terminal normalized result `SLOTS_AVAILABLE`.

The sanitized `TIMES` response contained allowed entries at `09:40`, `14:20`,
`14:40`, `15:20`, `15:40`, `16:00`, and `16:20`. The normalized
`available_time_slots_count` records seven allowed time entries rather than
the sum of the capacity values displayed in localized slot labels.

## Boundary and interpretation

The reviewed `getDays()` and `getTime()` call sites belong to the public
pre-identity workflow. Separately visible phone, OTP, fingerprint, CAPTCHA,
identity, and booking operations are outside the monitoring contract and were
not invoked or used as discovery evidence.

This observation independently confirms Kortrijk; it does not infer a rule
for future Belgian or other deployments. Additional deployments require
independent evidence and governance review.

## Governance status

The project owner approved the deployment-specific capability on 2026-08-04.
The corresponding [governance decision](../../docs/governance/2026-08-04-kortrijk-public-discovery-promotion.md)
authorizes only passive, fail-closed, HTTP-first public discovery with an
optional explicitly enabled experimental Playwright fallback after HTTP
`BLOCKED`, ending at `TIMES`.
