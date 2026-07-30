# Providers

Provider support is implemented through adapters. Each adapter translates one public appointment system into the project's normalized availability states.

Listing a provider in this document does not mean that production support is available.

## Provider acceptance principles

Before an adapter is added, the project should confirm that:

- the relevant appointment workflow is publicly available;
- monitoring can be performed without bypassing access controls;
- challenge and error states can be distinguished from valid availability responses;
- a responsible polling strategy can be defined;
- the adapter does not require passport numbers or document details;
- final registration remains on the official provider website.

## DP Document

**Research status:** Active feasibility study and local integration prototype

**First research location:** Kortrijk, Belgium

Frontend version 7.34.2 confirms this public, pre-authentication flow:

```text
Service -> form=days -> form=times
```

The days request requires `ServiceCenterId`, `ServiceId`, and a CSRF token.
The times request adds `Date`. Neither requires fingerprint generation,
authentication, personal data, OTP, BankID, Diia, or reservation submission.

Booking is separate:

```text
submitForm* -> browser fingerprint -> OTP / BankID / Diia -> reservation
```

Embedded ThumbmarkJS module 708 belongs to that booking flow and is
intentionally excluded from MonitorProvider. Normal monitoring is HTTP-only.
Browser automation is reserved for diagnostics, controlled reverse
engineering, or future booking research. A blocked request remains `BLOCKED`;
the monitor does not launch Playwright.

Discovery is evidence-first:

```text
LANDING
├── confirmed no-slots HTML -> NO_SLOTS, stop
├── blocked/error/unknown   -> unresolved state, stop
└── queue form + CSRF       -> guarded days transition
                                └── dates -> guarded times transition
```

The classifier emits typed evidence such as `HTTP_200`,
`HTML_NO_SLOTS_MARKER`, `QUEUE_FORM_FOUND`, and `CSRF_FOUND`. Absence of a form
alone is never evidence for `NO_SLOTS`.

The following items are not yet confirmed or implemented:

- stable capture of live availability data;
- normalized day and time-slot responses;
- confirmed CSRF field names and response schemas for every deployment;
- safe polling limits;
- live validation of the HTTP days/times adapter for each configured centre.

## Centre implementation status

| Centre | Implemented locally | Live evidence |
|---|---|---|
| Kortrijk | Landing-page monitor, Observation persistence, diagnostic outbox integration; separate HTTP `days`/`times` adapter methods exist but are not wired into the monitor loop | A historical 24-hour page-level study exists; the current HTTP-only full discovery flow still needs live validation |
| Berlin | Independent landing-page entry point using the shared city monitor | Offline tests only; centre-specific live classification is pending |
| Bratislava | Independent landing-page entry point using the shared city monitor | The owner observed separate date/time steps in a passive browser session on 2026-07-30; monitor classification and exact HTTP contract remain unvalidated |
| Milan | No repository monitor entry point | The owner observed comparable separate date/time steps on 2026-07-30; no implementation or deployment-specific HTTP contract is established |

The frontend findings describe the observed DP Document application. They do
not prove identical deployment details, markers, CSRF field names, or response
schemas at every centre.

The Bratislava/Milan evidence is
[user-provided live observation](../research/dp-document/2026-07-30-bratislava-milan-live-observation.md),
not repository-derived evidence or independently repeatable monitor
validation.

Until a deployment-specific CSRF input name is confirmed it remains explicit
configuration through `<PROVIDER>_CSRF_FIELD`; the monitor does not guess it.

## Public documentation boundary

Provider documentation describes observable workflow stages, supported states, limitations, and safety decisions. It must not include secrets, session data, CAPTCHA tokens, browser profiles, fingerprints, raw network captures, or detailed reproduction recipes for internal provider requests.
