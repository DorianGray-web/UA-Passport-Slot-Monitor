# Belgium — Kortrijk Technical Spike

## Current observed state

NO_SLOTS

## Official message

Наразі всі місця зайняті.

## Questions

- Is the status rendered server-side?
- Is there an availability API request?
- Does checking the initial page create a session?
- At which step does CAPTCHA appear?
- Can the state be checked without personal data?
- What changes when slots become available?

## Validated technical findings

### Updated frontend 7.34.2 findings

Deeper analysis supersedes the earlier assumption that ThumbmarkJS or a
persistent browser profile is required for queue discovery.

Public discovery is available before authentication through:

```text
Service -> form=days -> form=times
```

The requests use `ServiceCenterId`, `ServiceId`, CSRF, and `Date` for times.
They contain no fingerprint parameter.

Module 708 is an embedded ThumbmarkJS implementation. Its locally generated
fingerprint is appended only by `submitFormClassic`, `submitFormCombo`,
`submitFormBankID`, and `submitFormDiia`. Observed inputs include WebGL,
Canvas, OfflineAudioContext, installed fonts, browser detection, permissions,
media queries, and hardware properties. No call to `api.thumbmarkjs.com` was
observed during queue discovery.

The monitor must not generate or depend on fingerprints, and it must not use
Playwright for normal availability discovery.

### Historical page-access observations

The electronic queue page is delivered as server-rendered HTML with a
modular JavaScript application layered on top. The application uses
Webpack dynamic chunks, Alpine-style asynchronous components, and
ThumbmarkJS-based browser fingerprinting.

During the earlier experiment, a persistent Chromium profile was required to
retrieve the target content reliably. Requests made with a basic HTTP
client and a clean browser context returned HTTP 403, while a persistent
headed Chromium context successfully retrieved the target page.

The queue logic appears to be split into at least three variants:

- Neo
- Trinity
- Totoro

### Evidence

- The main Webpack bundle contains dynamic chunk mappings for
  `m-queue-logicneo`, `m-queue-logictrinity`, and
  `m-queue-logictotoro`.
- The main bundle includes ThumbmarkJS, but later call-site analysis confirms
  that it belongs to booking submission, not days/times discovery.
- A persistent Chromium profile returned HTTP 200 with target content,
  while a clean context returned HTTP 403.
