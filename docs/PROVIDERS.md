# Providers

Provider support is implemented through adapters. Each adapter translates one public appointment system into the project's normalized availability states.

Listing a provider in this document does not mean that production support is available.
The governance state of every configured deployment is tracked in the
[Evidence Matrix](EVIDENCE_MATRIX.md).

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
intentionally excluded from MonitorProvider. HTTP remains preferred. The nine
currently registry-enabled research profiles—Madrid, Barcelona, London,
Milan, Valencia, Berlin, Toronto, Cologne, and Bratislava—may use an explicitly enabled experimental
persistent-browser fallback after HTTP `BLOCKED`; it stops at public `TIMES`
and never interacts with CAPTCHA, identity, or booking. Kortrijk and Chisinau
remain landing-only.

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

Nine deployments now have evidence-confirmed and governance-approved public
date/time contracts. The following items remain incomplete:

- confirmed CSRF field names and response schemas for every deployment;
- production polling limits beyond the bounded research policy;
- live validation of the HTTP days/times adapter for each configured centre.

## Centre implementation status

| Centre | Implemented locally | Live evidence |
|---|---|---|
| Kortrijk | Shared `CityMonitor` landing-only entry point plus opt-in ADR-0011 candidate landing probe; no service is selected automatically | A historical 24-hour study, a 12-hour comparison, and the 2026-08-02 six-hour release validation exist. The latest candidate probe found no queue form or identifiers; service selection and full discovery remain unconfirmed |
| Berlin | Evidence-gated `berlin-v1` discovery profile (centre `2`, service `4`) | Owner-provided live evidence confirms `LANDING -> DAYS -> TIMES -> STOP`; the six-hour validation observed both `NO_SLOTS` and `SLOTS_AVAILABLE`, with no browser error or browser `UNKNOWN` |
| Bratislava | Evidence-gated `bratislava-v1` discovery profile (centre `9`, service `4`) | Owner-provided live evidence confirms the bounded public contract; the six-hour validation observed both `NO_SLOTS` and `SLOTS_AVAILABLE` |
| Milan | Experimental HTTP-first browser-fallback profile (`ServiceCenterId=4`, `ServiceId=4`) | Owner-provided passive browser evidence confirmed the public `form=days` request on 2026-07-31; the bounded runtime stops at `TIMES` |
| Madrid | Shared city-monitor entry point plus evidence-gated `madrid-v1` public `days`/`times` discovery; stops at `TIMES` | Owner-provided evidence confirms centre `6`, service `4`, and the public days and times response schemas |
| London | Experimental HTTP-first browser-fallback profile (`ServiceCenterId=47`, `ServiceId=4`) | Owner-provided passive browser evidence confirmed the public `form=days` request on 2026-07-31; the bounded runtime stops at `TIMES` |
| Toronto | Evidence-gated `toronto-v1` discovery profile (centre `46`, service `4`) | Owner-provided live evidence confirms the bounded contract; the six-hour validation observed both `NO_SLOTS` and `SLOTS_AVAILABLE`, with up to 30 available time entries |
| Chisinau | Shared city-monitor entry point and registry configuration | Owner-reported `NO_SLOTS` landing page; independent runtime validation pending |
| Barcelona | Independent entry point plus evidence-gated `barcelona-v1` HTTP discovery and opt-in persistent-browser fallback; stops at `TIMES` | Owner evidence confirms the contract; a bounded 2026-07-31 runtime check independently completed HTTP `403` -> Playwright `TIMES` and recorded `SLOTS_AVAILABLE` |
| Valencia | Independent entry point plus evidence-gated `valencia-v1` HTTP discovery and opt-in persistent-browser fallback; centre `7`, service `4`; stops at `TIMES` | Owner-provided passive browser evidence confirms the public days/times request sequence; the earlier 12-hour bounded runtime validation completed without browser error or browser `UNKNOWN` |
| Cologne | Evidence-gated `cologne-v1` discovery profile (centre `3`, service `4`) | Owner-provided live evidence confirms the bounded public contract and seven allowed time entries; the later six-hour validation remained `NO_SLOTS` in all 38 observations |

The frontend findings describe the observed DP Document application. They do
not prove identical deployment details, markers, CSRF field names, or response
schemas at every centre.

The Bratislava/Milan evidence is
[user-provided live observation](../research/dp-document/2026-07-30-bratislava-milan-live-observation.md),
not repository-derived evidence or independently repeatable monitor
validation.

The configurable multi-centre sample and control-group rationale are
documented in the
[2026-07-31 research plan](../research/dp-document/2026-07-31-multi-centre-live-monitoring.md).

The question of public calendar visibility before identity verification was
initially tracked in the
[pre-identity calendar research report](../research/dp-document/2026-07-31-pre-identity-calendar-research.md).
That historical report is superseded for Madrid, Barcelona, London, and Milan
by the implemented strict classifiers and the bounded four-centre validation.
The earlier
[eight-hour HTTP runtime validation](../research/dp-document/2026-07-31-eight-hour-http-runtime-validation.md)
remains evidence about HTTP behavior before the experimental browser transport
was enabled.

All nine enabled profiles reuse the strict confirmed response classifiers,
fail closed as `UNKNOWN` on protocol deviation, and terminate at `TIMES`. See the
[Barcelona live-observation report](../research/dp-document/2026-07-31-barcelona-live-observation.md),
the
[Valencia live-observation report](../research/dp-document/2026-08-01-valencia-live-observation.md),
the
[Berlin live-observation report](../research/dp-document/2026-08-01-berlin-live-observation.md),
the
[Toronto live-observation report](../research/dp-document/2026-08-01-toronto-live-observation.md),
the [Cologne live-observation report](../research/dp-document/2026-08-01-cologne-live-observation.md),
the [Bratislava live-observation report](../research/dp-document/2026-08-01-bratislava-live-observation.md),
the
[cross-deployment comparison](../research/dp-document/2026-08-01-cross-deployment-public-discovery-comparison.md),
and the local run-summary workflow documented in the project README.

Until a deployment-specific CSRF input name is confirmed it remains explicit
configuration through `<PROVIDER>_CSRF_FIELD`; the monitor does not guess it.

## Public documentation boundary

Provider documentation describes observable workflow stages, supported states, limitations, and safety decisions. It must not include secrets, session data, CAPTCHA tokens, browser profiles, fingerprints, raw network captures, or detailed reproduction recipes for internal provider requests.
