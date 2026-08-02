# Valencia Public Calendar Live Observation

**Evidence status:** User-provided passive browser observation  
**Observation date:** 2026-08-01  
**Deployment:** Valencia, Spain  
**Scope:** Public discovery only

## Provenance

The project owner observed the official Valencia DP Document queue page in a
normal browser and inspected the public requests and responses in developer
tools. This is user-provided live evidence. It is distinct from repository
fixtures, automated tests, and independently repeatable runtime validation.

No CSRF value, cookies, headers, browser storage, personal data, CAPTCHA data,
or raw network capture is retained in this report.

## Confirmed public contract

- queue URL: `https://valencia.pasport.org.ua/solutions/e-queue`;
- service centre: `7`;
- service: `4`;
- public date discovery uses `form=days`;
- public time discovery uses `form=times` and the selected date;
- date responses contain a `days` array with `datePart`, `date`, and
  `isAllowed` values;
- time responses contain a `timeSlots` array with `startTime`, `slot`, and
  `isAllowed` values;
- the delivered frontend filters both collections to entries whose
  `isAllowed` value is exactly `true`;
- an empty allowed collection is rendered as the provider's no-slots message;
- discovery is publicly observable before identity data or CAPTCHA
  interaction.

The delivered frontend also reads `allowedJobCount` when supplied for a date.
The field remains optional evidence and must not be inferred when absent.

## Monitoring boundary

The admitted research profile is:

```text
valencia-v1
LANDING -> DAYS -> TIMES -> STOP
```

HTTP remains the preferred transport. Persistent Playwright may run only when
the experimental fallback is explicitly enabled and HTTP is classified as
`BLOCKED`. Monitoring stops at `TIMES` and must not submit identity data,
interact with CAPTCHA, generate a fingerprint, or attempt booking.

## Validation status

The live evidence is sufficient to configure an evidence-gated Valencia
profile using the existing strict public-response classifiers. A bounded
multi-hour runtime comparison is still required to measure HTTP success,
fallback completion, timing, and stability for this deployment.
