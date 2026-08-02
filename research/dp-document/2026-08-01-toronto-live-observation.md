# Toronto Public Discovery Live Observation

**Evidence date:** 2026-08-01  
**Observed deployment:** Toronto, Canada  
**Source:** project-owner passive browser review, user-provided response
payload, and reviewed frontend source  
**Confirmed screenshot window:** 18:37:22–18:38:16 Europe/Amsterdam

## Scope and provenance

The project owner observed the official Toronto DP Document queue page in a
normal interactive browser. Screenshot filenames establish the observation
window. No identity data was submitted, CAPTCHA was not interacted with, and
no booking action was attempted.

Raw screenshots, cookies, and the observed CSRF value are not retained in the
repository. This note contains only sanitized reviewed conclusions.

## Observed live evidence

- `ServiceCenterId = 46`;
- `ServiceId = 4`;
- the landing response exposed the public queue form;
- `DAYS` returned one allowed date, `2026-08-31`;
- `TIMES` returned 11 entries, all with `isAllowed = true`;
- the earliest entry was `08:15:00` and the latest was `13:00:00`;
- the human-readable labels reported 32 free appointments in aggregate across
  those 11 time entries;
- discovery reached `SLOTS_AVAILABLE` and stopped at `TIMES`.

The complete user-provided JSON payload establishes the count and time range.
The aggregate value of 32 is derived from the free-slot counts embedded in the
11 `slot` labels; it is distinct from `available_time_slots_count`, which
counts time entries and therefore equals 11.

```text
LANDING
  -> DAYS (1 allowed date)
  -> TIMES (11 allowed entries; 08:15:00–13:00:00)
  -> SLOTS_AVAILABLE
  -> STOP
```

## Frontend-source evidence

Reviewed frontend code separately defines a public `serviceCheck()` request:

```text
form=check_services
ServiceCenterId
ServiceId
CSRF field
```

Its response field `days` controls whether the date selector is shown. This
confirms the operation and its client-side interpretation. The supplied live
screenshots confirm `days` and `times` responses, but do not independently
establish the live `check_services` response. These evidence classes remain
separate.

## Trust classification

**Observed evidence:** centre `46`, service `4`, one allowed date, 11 allowed
time entries from `08:15:00` through `13:00:00`, and the terminal public
boundary. The response labels report 32 free appointments in aggregate.

**Confirmed capability:** Toronto has a reviewed public discovery contract
through `TIMES -> STOP`.

**Inference:** none is required to classify the observed result as
`SLOTS_AVAILABLE`.

**Generalization:** none. The evidence does not establish identical
identifiers, preflight requirements, or availability behaviour for Kortrijk,
Bratislava, Chisinau, or future deployments.

Under ADR-0011, this confirmed research evidence supports a separate
governance decision. It does not modify `providers.json`, enable browser
fallback, or otherwise change Toronto runtime capability by itself.

> **Supersession note — 2026-08-02:** `toronto-v1` was approved independently
> and added to `providers.json` for centre `46`, service `4`. The original
> observation remains unchanged.
