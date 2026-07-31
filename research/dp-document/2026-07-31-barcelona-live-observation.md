# Barcelona Public Calendar Live Observation — 2026-07-31

## Evidence provenance

- source: user-provided passive browser observation;
- observed deployment: Barcelona;
- page: `https://barcelona.pasport.org.ua/solutions/e-queue`;
- frontend family observed: DP Document 7.34.2;
- evidence type: browser developer-tools screenshots supplied by the project
  owner;
- repository status: summarized evidence only; raw screenshots and dynamic
  request values are not committed.

This evidence is distinct from repository-derived frontend analysis, offline
tests, fixtures, and independently repeatable monitor validation.

## Confirmed public protocol

The observation confirms:

```text
LANDING -> DAYS -> TIMES -> STOP
```

Confirmed centre configuration:

```text
ServiceCenterId = 41
ServiceId = 4
CSRF submitted value = 1
CSRF field name = dynamic landing-provided opaque value
```

The `days` response contained a `days` array with `datePart`, `date`, and
`isAllowed`. The `times` request added the selected ISO `Date`; its response
contained a `timeSlots` array with `startTime`, `slot`, and `isAllowed`.

These shapes match the confirmed Madrid public response contract. This
supports reuse of strict response classifiers while retaining a separate
`barcelona-v1` evidence profile.

## Boundary

No identity data was submitted. No CAPTCHA was completed or bypassed. No
booking or reservation was attempted. Discovery ended after public time slots
became observable.

The opaque CSRF field shown during the session is transient evidence and must
not be stored in documentation, configuration, Observation, fixtures, or
logs. Runtime discovery extracts it from each current landing response.

## Independent runtime validation

At `2026-07-31T11:39:13Z` (`13:39:13` Europe/Amsterdam), one bounded runtime
check exercised the experimental HTTP-first browser fallback:

```text
HTTP landing 403
    -> persistent Playwright landing 200
    -> days 200
    -> times 200 for each confirmed date
    -> STOP
```

The immutable Observation recorded:

- state: `SLOTS_AVAILABLE`;
- transport: `playwright`;
- discovery stage: `TIMES`;
- available dates: `12`;
- allowed public time entries: `325`;
- earliest time: `10:00:00`;
- latest time: `18:30:00`;
- total cycle duration: `10,538 ms`.

The sanitized trace contains the initial HTTP `403`, browser landing `200`,
one `days` response, and twelve `times` responses. The persistent browser
closed immediately after TIMES. No CAPTCHA, identity, continuation, or booking
control was used. This is runtime-derived evidence and is distinct from the
earlier owner-provided screenshots.
