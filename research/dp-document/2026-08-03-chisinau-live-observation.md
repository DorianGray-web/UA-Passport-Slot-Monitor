# Chisinau Live Public-Discovery Observation

**Observation date:** 2026-08-03

**Evidence source:** Project-owner live browser review

## Observed facts

- Deployment: `https://chisinau.pasport.org.ua/solutions/e-queue`.
- `ServiceCenterId=45` and `ServiceId=4` were recorded in the public `TIMES`
  request payload.
- The public queue form loaded successfully over HTTP 200.
- `DAYS` returned 25 allowed dates from `2026-09-04` through `2026-10-02`.
- The selected date `2026-09-08` produced a recognized, non-empty
  `timeSlots` response containing allowed public time entries.
- The reviewed flow reached the bounded public sequence:

```text
LANDING -> DAYS -> TIMES -> STOP
```

- No identity information was submitted.
- No CAPTCHA, OTP, reservation, or booking action was performed.

## Interpretation

The live evidence confirms the same bounded high-level public contract already
reviewed for the other governed profiles. It confirms Chisinau only; it does
not establish a protocol guarantee for Kortrijk or future deployments.
