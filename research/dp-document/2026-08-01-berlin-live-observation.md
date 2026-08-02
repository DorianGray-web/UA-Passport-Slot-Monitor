# Berlin Public Discovery Live Observation

**Evidence date:** 2026-08-01  
**Observed deployment:** Berlin, Germany  
**Source:** project-owner passive browser review  
**Confirmed screenshot window:** 13:03:24–13:04:59 Europe/Amsterdam

## Scope and provenance

The project owner observed the official Berlin DP Document queue page through
a normal interactive browser. Screenshot filenames establish the observation
window. The review stopped at public availability discovery and did not submit
identity data, interact with CAPTCHA, or attempt booking.

Raw screenshots and the observed CSRF value are not repository evidence. This
note retains only the sanitized, reviewed conclusions supplied by the project
owner.

## Observed evidence

- `ServiceCenterId = 2`;
- `ServiceId = 4`;
- the public queue form was exposed after a successful landing response;
- public discovery followed `LANDING -> DAYS -> TIMES`;
- `DAYS` returned one allowed date, `2026-08-31`;
- the date-dependent `TIMES` response returned `{"timeSlots": []}`;
- discovery stopped at the public `TIMES` boundary.

The normalized result is:

```text
discovery_stage = TIMES
available_dates_count = 1
available_time_slots_count = 0
state = NO_SLOTS
```

This is not landing-level `NO_SLOTS`. The observed transition was:

```text
LANDING
  -> DAYS (1 allowed date)
  -> TIMES (0 available slots)
  -> NO_SLOTS
  -> STOP
```

## Trust classification

**Observed evidence:** the request fields, allowed-date response, empty
`timeSlots` response, and terminal public boundary described above.

**Confirmed capability:** Berlin has a reviewed public discovery contract for
centre `2`, service `4`, through `TIMES -> STOP`.

**Inference:** the date may have lost all usable time entries before or during
the short observation window. This interpretation is plausible but is not
required for the `NO_SLOTS` classification.

**Generalization:** none. The evidence does not establish behaviour for
Kortrijk, Bratislava, Chisinau, Toronto, or any future deployment.

Under ADR-0011, this confirmed research evidence supports a separate
governance decision about registry capabilities. It does not modify
`providers.json` or runtime behaviour by itself.

## Cross-deployment context

Across the currently evidence-confirmed deployments—Madrid, Barcelona,
London, Milan, Valencia, and Berlin—successful HTTP `200` landing responses
exposed the public queue form, and public discovery proceeded through `DAYS`
and `TIMES` before stopping. This is a bounded statement about the retained
evidence corpus, not a guarantee about all DP Document deployments.

## Later availability observation

**Confirmed screenshot window:** 19:27:05–19:27:13 Europe/Amsterdam  
**Source:** project-owner passive browser review and user-provided complete
`timeSlots` payload

Later on the same day, the Berlin deployment again exposed the public form for
the same allowed date, `2026-08-31`. The complete `TIMES` response contained
9 entries, all with `isAllowed = true`:

- earliest time: `15:15:00`;
- latest time: `17:15:00`;
- `available_time_slots_count = 9`;
- the human-readable labels reported 61 free appointments in aggregate;
- terminal state: `SLOTS_AVAILABLE` at `TIMES -> STOP`.

The aggregate value of 61 is derived from the counts embedded in the `slot`
labels. It is distinct from the normalized count of 9 time entries.

The live request payload independently confirmed these non-secret fields:

```text
form = times
ServiceCenterId = 2
ServiceId = 4
Date = 2026-08-31
```

The request also contained the deployment's dynamic CSRF field. Its name and
value are intentionally not retained in repository documentation.

```text
Earlier: LANDING -> DAYS (1) -> TIMES (0) -> NO_SLOTS -> STOP
Later:   LANDING -> DAYS (1) -> TIMES (9) -> SLOTS_AVAILABLE -> STOP
```

### Interpretation boundary

**Observed evidence:** the same allowed date produced zero time entries in the
earlier review and nine allowed time entries in the later review.

**Inference:** availability changed during the interval between reviews. The
evidence does not establish whether this resulted from a scheduled release,
cancellation, cache transition, or another provider-side cause.

**Generalization:** none. The observation establishes temporal variability for
Berlin on this date only.

### Frontend boundary corroboration

Reviewed frontend source separately confirms `check_services`, `days`, and
`times` as public operations using centre, service, CSRF, and date where
applicable. The same source places phone validation, CAPTCHA token,
fingerprint, OTP, and reservation checks inside `submitFormClassic()` after
public time selection. This corroborates the existing monitoring boundary;
none of those booking fields or operations were used during the live review.

> **Supersession note — later on 2026-08-01:** Toronto subsequently became a
> seventh evidence-confirmed deployment. This does not alter the Berlin
> observations above or generalize the contract to other deployments.

> **Supersession note — 2026-08-02:** `berlin-v1` was approved independently
> and added to `providers.json` for centre `2`, service `4`. The retained
> observations and their bounded interpretation remain unchanged.
