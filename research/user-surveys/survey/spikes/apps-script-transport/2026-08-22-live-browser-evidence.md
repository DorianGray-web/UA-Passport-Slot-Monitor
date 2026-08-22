# Apps Script Transport Live Browser Evidence

**Status:** user-provided live-experiment evidence
**Observation date:** 2026-08-22
**Probe version:** `1.0.0`
**Persistence:** none

## Research question

Can a browser page served from the survey's GitHub Pages HTTPS spike origin
send a non-persistent request to a temporary Google Apps Script Web App and
read an application-level ContentService acknowledgement after the platform
redirect, without an intermediate proxy?

This question is limited to transport feasibility. It does not evaluate or
select a production backend, storage implementation, or ADR-0014 policy.

## Provenance and evidence classes

The project owner supplied the sanitized results of a live Chrome experiment.
No live request was repeated while preparing this report. The temporary
Apps Script deployment URL, deployment identifier, complete redirected URLs,
and ephemeral capability query values are not retained.

This report uses these classes:

- **DOCUMENTED:** stated by official Google Apps Script documentation;
- **OBSERVED:** present in the supplied browser/network/application evidence;
- **INFERRED:** a bounded conclusion derived from documented and observed facts;
- **NOT PROVEN:** not established by the retained evidence;
- **NOT SUPPORTED:** contradicted as a necessary conclusion for the tested
  configuration, without asserting a universal platform rule.

## Probe design

The isolated probe used the repository's `Code.gs` and browser harness. The
server returned JSON through `ContentService` and performed no persistence.
The request carried only probe metadata. `RECEIVED` and `INVALID_PROBE` are
probe-only results and are not ADR-0014 submission outcomes.

The tested readable POST used:

- Fetch method `POST`;
- Fetch mode `cors`;
- `Content-Type: text/plain`;
- a JSON-encoded body;
- `probe_version: "1.0.0"`;
- `request_id: "test_post_cors_valid"`.

GET used mode `cors` with the probe version and request ID in query
parameters. A separate POST used `no-cors` to measure opaque browser behavior.

## Observed environment

| Dimension | Observed value | Classification |
| --- | --- | --- |
| Source | Survey spike on a GitHub Pages HTTPS origin | OBSERVED |
| Target | Temporary Apps Script Web App `/exec` deployment | OBSERVED |
| Browser | Chrome; exact version not recorded | OBSERVED / limitation |
| Application response | ContentService JSON | OBSERVED |
| Redirect | `/exec` response path included HTTP 302 | OBSERVED for this experiment |
| Redirect target | `script.googleusercontent.com` | DOCUMENTED + OBSERVED |
| Final response | HTTP 200 | OBSERVED for this experiment |
| Deployment access and execute-as settings | Not retained in supplied evidence | NOT PROVEN |

Google documents that Apps Script Web Apps dispatch GET and POST requests to
`doGet(e)` and `doPost(e)`. Google also documents that ContentService output is
redirected for security to a one-time URL on `script.googleusercontent.com`.

## Valid POST observation

The browser observed a Fetch response with type `cors`, status 200,
`redirected: true`, final host `script.googleusercontent.com`, and a readable
response body. The returned application response was:

```json
{
  "probe_version": "1.0.0",
  "probe_result": "RECEIVED",
  "method": "POST",
  "request_id": "test_post_cors_valid",
  "content_type": "text/plain",
  "content_length": 61,
  "received_at": "2026-08-22T13:42:06.726Z",
  "persistent_side_effect": false
}
```

Because this response can only be constructed after `doPost(e)` reads and
parses `e.postData.contents`, it is application-level OBSERVED evidence that:

- the valid request reached `doPost(e)`;
- the submitted body reached `e.postData.contents`;
- the JSON encoded as `text/plain` was parsed server-side;
- the request ID survived the tested transport path;
- the tested GitHub Pages origin could read the application acknowledgement
  after the ContentService redirect.

## Valid GET observation

The browser independently observed a Fetch response with type `cors`, status
200, `redirected: true`, final host `script.googleusercontent.com`, and a
readable response body:

```json
{
  "probe_version": "1.0.0",
  "probe_result": "RECEIVED",
  "method": "GET",
  "request_id": "test_get_cors_valid",
  "content_type": null,
  "content_length": -1,
  "received_at": "2026-08-22T13:43:06.729Z",
  "persistent_side_effect": false
}
```

This is OBSERVED evidence of a readable GET application acknowledgement in
the same tested origin/deployment configuration.

## `no-cors` POST observation

The earlier `no-cors` POST produced an opaque Fetch response with status 0.
This is OBSERVED evidence only that browser dispatch was attempted. It does
not expose response headers or content and does not prove server receipt,
application processing, success, or persistence.

## Invalid-probe observations

Earlier inconsistent requests returned readable final responses with HTTP
200 and probe result `INVALID_PROBE`. Observed codes included:

- GET: `unsupported_probe_version`;
- POST: `invalid_json`;
- POST: `unsupported_probe_version`.

These observations show that HTTP 200 alone did not identify the probe-level
application result. The readable response body distinguished `RECEIVED` from
`INVALID_PROBE`. This does not select production HTTP or outcome mapping.

## Evidence matrix

| Claim | Classification | Evidence boundary |
| --- | --- | --- |
| Apps Script `/exec` ContentService output redirects | DOCUMENTED + OBSERVED | Official documentation and tested response path |
| Redirect target host is `script.googleusercontent.com` | DOCUMENTED + OBSERVED | Official documentation and final observed host |
| Tested `/exec` response path included HTTP 302 | OBSERVED | This experiment only |
| Final tested ContentService response returned HTTP 200 | OBSERVED | This experiment only |
| Valid POST reached `doPost(e)` | OBSERVED | `RECEIVED` POST response from probe code |
| POST body reached `e.postData.contents` | OBSERVED | Parsed body fields affected returned acknowledgement |
| JSON carried as `text/plain` was parsed server-side | OBSERVED | Valid POST `RECEIVED` response |
| `request_id` survived the transport | OBSERVED | Matching returned request ID |
| GitHub Pages to Apps Script response was CORS-readable | OBSERVED | Tested origin, Chrome, deployment, and redirect path only |
| Valid GET produced a readable application acknowledgement | OBSERVED | Tested configuration only |
| Valid POST produced a readable application acknowledgement | OBSERVED | Tested configuration only |
| `no-cors` Fetch response was opaque with status 0 | OBSERVED | Earlier no-cors run |
| Opaque response proves server receipt | NOT PROVEN | Opaque response exposes no acknowledgement |
| HTTP 200 alone represents application success | NOT SUPPORTED | Both `RECEIVED` and `INVALID_PROBE` were returned with HTTP 200 |
| A proxy is required solely for readable browser-to-Apps-Script transport | NOT SUPPORTED | Not required in the tested configuration |
| The tested path can provide readable application acknowledgement without a proxy | INFERRED | Bounded to the observed configuration |

## Evidence-supported conclusion

In the 2026-08-22 live experiment, the tested GitHub Pages origin successfully
sent a POST using Fetch mode `cors`, `Content-Type: text/plain`, and a
JSON-encoded body to the tested Apps Script Web App. Chrome received and read a
ContentService JSON application acknowledgement after the Apps Script
redirect.

Therefore, an intermediate proxy was not required solely to obtain readable
browser-to-Apps-Script acknowledgement in this observed configuration. This
is a bounded feasibility conclusion, not an Apps Script production-backend
selection or a universal claim that all Apps Script deployments support the
same cross-origin behavior.

## Limitations and non-claims

This experiment does not establish:

- Apps Script or Google Sheets as production components;
- `SurveyResponse v2` transport or authoritative server validation;
- persistence, concurrency, LockService, or idempotency behavior;
- retry, timeout, quota, availability, or production-scale reliability;
- production privacy, security, logging, retention, or deletion suitability;
- a production HTTP method, media type, status, redirect, or CORS policy;
- behavior across other browsers, origins, Apps Script deployments, access
  configurations, accounts, or platform changes.

## Relationship to ADR-0014 and next boundary

This evidence addresses the OPEN Apps Script browser/deployment feasibility
question for one tested configuration. It does not resolve ADR-0014's OPEN
production choices and does not change its five semantic outcomes.

The next separately approved research boundary would evaluate an
adapter-specific profile, including authoritative validation and observable
canonical outcomes, before any persistence experiment. Storage, Sheets,
locking, idempotency, retry, timeout, privacy lifecycle, and production
deployment remain outside this completed transport spike.

## Documented sources

- [Apps Script Web Apps](https://developers.google.com/apps-script/guides/web)
- [Apps Script Content Service and redirects](https://developers.google.com/apps-script/guides/content)
