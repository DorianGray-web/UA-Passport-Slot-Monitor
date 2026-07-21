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

The electronic queue page is delivered as server-rendered HTML with a
modular JavaScript application layered on top. The application uses
Webpack dynamic chunks, Alpine-style asynchronous components, and
ThumbmarkJS-based browser fingerprinting.

During the experiment, a persistent Chromium profile was required to
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
- The main bundle includes ThumbmarkJS and stores a browser identifier
  in the `dpuniq` cookie.
- A persistent Chromium profile returned HTTP 200 with target content,
  while a clean context returned HTTP 403.
