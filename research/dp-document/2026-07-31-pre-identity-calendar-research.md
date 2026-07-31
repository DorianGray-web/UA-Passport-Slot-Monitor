# Pre-identity Appointment Calendar Research — 2026-07-31

> **Historical; superseded in part — 2026-07-31:** This report preserves the
> evidence and conclusions available before public days/times discovery was
> implemented. Madrid, Barcelona, London, and Milan now have evidence-gated
> profiles that can reach `TIMES` and stop. HTTP remains preferred; an
> explicitly enabled experimental Playwright transport may run only after HTTP
> `BLOCKED`. The identity-boundary classifier remains unimplemented. The
> original observations and recommendations below are not rewritten.

## Research question

Does the DP Document public workflow expose service selection, appointment
dates, appointment times, or an appointment count before identity
verification?

The research boundary ends at the first identity-verification requirement.
No personal information, identity action, booking submission, CAPTCHA bypass,
or reservation action is permitted.

## Reference workflow

The project-owner observation from 2026-07-30 is the reference workflow:

```text
Landing
  -> Service selection
  -> Date selection
  -> Time selection
  -> Identity verification
  -> Booking
```

User-provided evidence established separate date and time request steps in
Bratislava and Milan and reported that time discovery followed selection of a
date. It did not establish selectors, response schemas, endpoint equality, or
the exact identity-boundary page. See
[Bratislava and Milan Live Observation](2026-07-30-bratislava-milan-live-observation.md).

Repository-derived frontend analysis independently establishes this logical
separation:

```text
public discovery: Service -> form=days -> form=times
booking:          submitForm* -> fingerprint -> identity/reservation
```

The `submitForm*` boundary is therefore the latest known point at which the
public discovery flow must stop. This is a code-path boundary, not proof that
every deployment currently exposes dates or times.

## Current implementation review

The repository contains two incomplete layers:

1. `DPDocumentHTTPMonitorProvider` implements HTTP landing, `form=days`, and
   `form=times` requests.
2. The active city monitor loops call only a landing-page GET and
   `LandingPageClassifier`.

`DiscoveryEngine` can permit a guarded transition after landing and after a
non-empty date set, but it intentionally does not classify days or times
payloads. No fixture-backed `DaysResponseClassifier` or
`TimesResponseClassifier` exists.

Consequently, the current runtime never reaches the same date/time stages
described by the owner-provided live observation.

## Controlled live check

### Method

Two passive checks targeted:

```text
https://bratislava.pasport.org.ua/solutions/e-queue
```

1. A direct HTTP GET.
2. A clean, temporary, headless Chromium context.

The browser probe performed one navigation and no clicks or form submissions.
It did not use a persistent profile, enter data, attempt identity verification,
or invoke booking.

Local evidence was written under the Git-ignored directory:

```text
artifacts/public-calendar-probe/2026-07-31-bratislava/
    bratislava-landing.png
    bratislava-landing.html
    bratislava-dom-fragments.json
    bratislava-network-summary.json
    bratislava-capture-summary.json
```

### Result

Both checks received HTTP `403`.

The browser displayed a Cloudflare security-verification page with a visible
“confirm that you are human” control. The provider queue form was not reached.

Evidence:

- page title: `Трохи зачекайте…`;
- HTTP status: `403`;
- body hash: observed locally but not retained in the public summary;
- relevant provider DOM fragment count: `0`;
- interaction count: `0`;
- form-submission count: `0`;
- identity verification attempted: `false`;
- booking attempted: `false`.

The raw HTML and screenshot are local research artifacts and must not be
committed. Challenge-specific network paths are redacted in the summary.

## Subsequent eight-hour runtime validation

A later approximately eight-hour HTTP monitoring session superseded the
blocked-only view of transport behavior for Madrid and Milan. Both centres
intermittently returned HTTP `200` with `QUEUE_FORM_FOUND`,
`SERVICE_CENTER_FOUND`, and `UNRECOGNIZED_HTML` evidence. The runtime therefore
reached their public queue forms, but correctly retained `UNKNOWN` because the
observed HTML version has no confirmed classifier.

This does not demonstrate that the active monitor executed `DAYS` or `TIMES`.
It narrows the current limitation to classifier coverage at the successful
public-form response. See
[Eight-Hour HTTP Runtime Validation](2026-07-31-eight-hour-http-runtime-validation.md).

## Evidence table

| State or stage | Evidence source | Result |
|---|---|---|
| `BLOCKED` | 2026-07-31 direct HTTP and clean Chromium | Confirmed for this session |
| Provider landing form | Current live check | Not reached |
| Service selection | 2026-07-30 owner observation and frontend analysis | Reported/architecturally supported; no selector captured in this session |
| Available dates | 2026-07-30 owner observation | Reported; no independently captured payload or DOM fixture |
| Available times | 2026-07-30 owner observation | Reported; dependent on a selected date; no independently captured payload or DOM fixture |
| Appointment count | None | Not confirmed |
| Identity boundary | Frontend `submitForm*` separation | Logical boundary confirmed; exact rendered page/selectors not captured |

## A/B conclusion

The hypothesis has a stage-dependent answer.

### A — landing is intentionally terminal

This is true when the landing response contains positive terminal evidence,
such as the recognized `NO_SLOTS` marker, or when access is `BLOCKED`. The
monitor must stop without issuing days/times requests.

### B — additional public stages exist

This is supported when landing evidence is `DISCOVERY_READY`. The documented
workflow and HTTP provider contract contain public days and times operations,
but the active monitor loop does not execute them. The state machine therefore
ends too early for discovery-ready responses.

The initial Bratislava check cannot independently confirm B because it was
blocked before the provider landing form. The subsequent Madrid and Milan
runtime evidence confirms that the HTTP monitor can reach a public form, but
it still does not confirm execution or classification of `DAYS` or `TIMES`.
Neither result may be used to claim that dates or times were absent.

## Selector status

Confirmed landing selectors already used by the repository:

```css
form
[name="ServiceCenterId"]
[name="ServiceId"]
meta[name="csrf-token"]
```

The CSRF input selector is deployment-configured.

No date, time, appointment-count, or identity-boundary selector is confirmed.
Candidates such as `[name="Date"]`, `[data-date]`, `[data-time]`, or
calendar-related classes remain hypotheses until captured in sanitized,
fixture-backed evidence. They must not be added to production classifiers
based on naming guesses.

## Recommendation

Retain HTTP-first monitoring. The eight-hour runtime validation confirms that
the transport can reach public queue forms intermittently and that the next
limitation is confirmed classifier coverage. Do not add browser automation to
the runtime.

The next authorized research session should:

1. use the owner's manually accessible public browser session;
2. capture the provider page after service selection;
3. capture redacted `days` and `times` response fixtures;
4. record stable DOM semantics rather than presentation-only class names;
5. capture the first identity-required page without interacting with it;
6. stop immediately;
7. record whether an appointment count is explicitly present.

Implementation should start only after those fixtures support deterministic
days, times, and identity-boundary classifiers.
