# Apps Script transport feasibility probe

**Status:** transport feasibility positively observed for one tested configuration;
not approved for production

This directory measures browser-visible Google Apps Script Web App behavior.
It is not a backend adapter, production transport, or implementation of
ADR-0014. It does not accept `SurveyResponse v2`, validate survey fields,
produce canonical submission outcomes, or persist anything.

## Completed live experiment

The 2026-08-22 Chrome experiment used the GitHub Pages HTTPS spike origin and
a temporary Apps Script Web App deployment. In that configuration, valid GET
and `text/plain` POST requests produced readable ContentService JSON
acknowledgements after redirecting to `script.googleusercontent.com`.

This is bounded feasibility evidence, not a universal Apps Script CORS claim
or a production-backend decision. See the sanitized
[live browser evidence report](2026-08-22-live-browser-evidence.md) for the
observations, evidence classifications, limitations, and non-claims. The
temporary deployment URL and redirect capability parameters are intentionally
not retained.

## Safety boundary

- `Code.gs` uses only `ContentService` and current time.
- It does not call Google Sheets, Drive, Properties, Cache, Lock, logging, or
  external network services.
- It never echoes a POST body and accepts at most 4096 characters.
- The harness sends only a random probe ID, probe version, timestamp, and
  constant marker.
- The harness does not use cookies, analytics, local storage, session storage,
  remote logging, automatic retry, or a client timeout.
- Do not enter a production endpoint, canonical survey response, personal
  data, secret, credential, or deployment URL into committed evidence.

`RECEIVED` and `INVALID_PROBE` are probe-only labels. They are not replacements
for `ACCEPTED`, `DUPLICATE_ACCEPTED`, `INVALID_REQUEST`,
`UNSUPPORTED_CONTRACT`, or `TEMPORARY_FAILURE`.

## Manual probe setup

1. Create a standalone Apps Script project for disposable feasibility testing.
2. Paste `Code.gs` into the project.
3. Deploy it as a Web App using a test-only deployment.
4. Record the chosen execute-as and access settings separately as experiment
   inputs; this spike does not prescribe them.
5. Do not commit the deployment URL.
6. Serve `harness/` through an HTTP(S) static server. Do not open it as a
   `file:` URL.
7. Enter the temporary `/exec` URL and run each probe once.

Apps Script `ContentService` redirects responses to a one-time
`script.googleusercontent.com` URL. The harness follows redirects and records
only the final origin, not the full redirected URL.

## Evidence matrix

Run from the intended GitHub Pages origin and record sanitized results for:

| Probe | What it can establish | What it cannot establish |
| --- | --- | --- |
| GET, `cors` | Whether the browser can read a redirected JSON response | POST feasibility or production semantics |
| POST `text/plain`, `cors` | Whether a simple POST yields a readable redirected JSON response | Validation, persistence, idempotency, or approved media type |
| POST `text/plain`, `no-cors` | Whether the browser permits an opaque dispatch attempt | Receipt, response content, success, or persistence |

For each run record browser/version, harness origin, deployment access mode,
probe kind, response type/status, redirect flag, final origin, duration, and
sanitized console/network errors. Do not record full deployment URLs, request
bodies, IP addresses, User-Agent strings, or raw platform logs.

## Interpretation gate

A readable probe response is feasibility evidence only. An opaque response or
resolved `fetch()` is not proof of server receipt. A failed readable response
does not justify a CORS workaround or contract change. Results must be reviewed
against ADR-0014 before choosing HTTP method, media type, response mapping,
origin policy, timeout, retry, deployment, validation, idempotency, logging, or
storage behavior.
