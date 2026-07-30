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

**Research status:** Active feasibility study

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

Until a deployment-specific CSRF input name is confirmed it remains explicit
configuration through `<PROVIDER>_CSRF_FIELD`; the monitor does not guess it.

## Public documentation boundary

Provider documentation describes observable workflow stages, supported states, limitations, and safety decisions. It must not include secrets, session data, CAPTCHA tokens, browser profiles, fingerprints, raw network captures, or detailed reproduction recipes for internal provider requests.
