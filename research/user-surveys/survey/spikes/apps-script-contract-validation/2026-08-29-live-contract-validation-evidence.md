# Apps Script adapter-profile contract-validation evidence

- **Date:** 2026-08-29
- **Status:** Completed bounded research experiment
- **Harness origin:** Local HTTP origin (`127.0.0.1`)
- **Adapter:** Temporary Google Apps Script Web App
- **Storage:** Disposable Google Sheet configured for synthetic fixtures only
- **Production status:** Not selected, approved, or implemented

## Evidence classes

- **DOCUMENTED** — behavior defined by the reviewed experimental implementation.
- **OBSERVED** — sanitized browser output returned by the live matrix.
- **INFERRED** — the narrow interpretation supported by those observations.
- **NOT PROVEN** — a plausible conclusion not established by this run.
- **NOT SUPPORTED** — a conclusion outside or contrary to the experiment boundary.
- **OPEN** — behavior deliberately left without canonical semantics.

No deployment URL, redirect capability URL, spreadsheet ID, account identifier,
real survey response, or personal data is retained in this report.

## Research question

The experiment asked whether a bounded Apps Script adapter profile could receive
a canonical `survey_response/2.0.0` encoded as JSON in a `text/plain` POST,
validate relevant contract requirements server-side, reject invalid input before
disposable persistence, use canonical `response_id` at the tested duplicate
boundary, and expose the five existing ADR-0014 semantic outcomes in a readable
browser response without changing SurveyResponse v2.

The run also exercised the canonically OPEN condition in which an existing
`response_id` is resubmitted with non-equivalent content. The spike was required
to detect that condition without overwriting, appending, or inventing a sixth
canonical outcome.

## Experimental configuration

**DOCUMENTED:** The implementation under this directory used:

- a synthetic fixture validated locally against the committed canonical JSON
  Schema before deployment;
- the generated `ContractSnapshot.gs` plus the explicitly limited schema-keyword
  interpreter in `Code.gs`;
- browser Fetch with `mode: "cors"`, `Content-Type: text/plain;charset=UTF-8`,
  and a JSON-encoded request body;
- a temporary Apps Script ContentService response;
- a ScriptLock-protected lookup and conditional append;
- disposable two-column storage containing only `response_id` and a canonical
  payload SHA-256 value; and
- no automatic retry, backoff, client timeout, analytics, telemetry, or browser
  persistence.

**OBSERVED:** The supplied browser evidence came from Chrome with the harness
served from `127.0.0.1`. It did not identify the Apps Script execute-as/access
settings and did not include a direct post-run Sheet inspection.

## Live matrix observations

All ten cases returned HTTP 200 responses with `response.type = "cors"`,
`redirected = true`, and sanitized final host `script.googleusercontent.com`.
HTTP 200 is transport evidence only; the application result came from the
experimental response body.

| Case | Controlled input | Expected | Observed | Duration (ms) | Classification |
| ---: | --- | --- | --- | ---: | --- |
| 1 | Valid canonical response | `ACCEPTED` | `ACCEPTED` | 4419 | `PASS` |
| 2 | Exact in-memory repeat | `DUPLICATE_ACCEPTED` | `DUPLICATE_ACCEPTED` | 2674 | `PASS` |
| 3 | Malformed JSON | `INVALID_REQUEST` | `INVALID_REQUEST` | 1108 | `PASS` |
| 4 | Missing required nullable property | `INVALID_REQUEST` | `INVALID_REQUEST` | 896 | `PASS` |
| 5 | Invalid `response_id` UUID | `INVALID_REQUEST` | `INVALID_REQUEST` | 4510 | `PASS` |
| 6 | Unknown centre taxonomy ID | `INVALID_REQUEST` | `INVALID_REQUEST` | 1233 | `PASS` |
| 7 | Wrong schema-defined field type | `INVALID_REQUEST` | `INVALID_REQUEST` | 980 | `PASS` |
| 8 | Unsupported `contract_version` | `UNSUPPORTED_CONTRACT` | `UNSUPPORTED_CONTRACT` | 1000 | `PASS` |
| 9 | Controlled transient failure | `TEMPORARY_FAILURE` | `TEMPORARY_FAILURE` | 1848 | `PASS` |
| 10 | Same identity, different content | OPEN spike-only observation | `OPEN_IDENTITY_CONTENT_CONFLICT` | 3814 | `OPEN` |

### Case 1 — accepted canonical response

**OBSERVED:** The server returned `ACCEPTED` for synthetic response ID
`4dbb8dc5-3eac-4d7d-afad-cb6f9b3f5e3e`. Its diagnostic reported
`validated_identity_hash_recorded`, one physical record for that identity, and
`persistence_effect: one_disposable_record`.

### Case 2 — exact repeat

**OBSERVED:** The harness reused the same response ID and exact in-memory Case 1
content. The server returned `DUPLICATE_ACCEPTED`; its diagnostic again reported
one physical record and `persistence_effect: none`.

**INFERRED:** In this tested execution path, the protected identity/hash lookup
distinguished an equivalent repeat and avoided a second append.

### Cases 3–7 — invalid input

**OBSERVED:** Malformed JSON returned diagnostic `malformed_json`. The four
schema-covered negative fixtures returned `schema_validation_failed` and
identified, respectively:

- missing required `$.answers.appointment_urgency`;
- UUID pattern and format failure at `$.response_id`;
- an unknown value at `$.answers.centre_ids[0]`; and
- a wrong container type involving `$.answers.problem_category_ids`.

Case 7 also returned an additional `wrong_type` diagnostic for
`$.answers.other_problem_text`. The intended wrong-type mutation was still
detected and the application outcome was `INVALID_REQUEST`; this run does not
establish why the limited experimental interpreter emitted the additional
diagnostic path.

Every response reported `persistence_effect: none`.

### Case 8 — unsupported contract

**OBSERVED:** Changing only `contract_version` produced
`UNSUPPORTED_CONTRACT`, diagnostic `unsupported_contract_version`, and no
reported persistence effect. The adapter profile therefore kept the version
gate distinct from ordinary invalid-request classification in this run.

### Case 9 — controlled transient failure

**OBSERVED:** The out-of-band spike-only control returned `TEMPORARY_FAILURE`
with diagnostic `controlled_transient_before_persistence`,
`control_scope: SPIKE_ONLY`, and `persistence_effect: none`.

This deterministic control did not exercise real platform failure, quota
exhaustion, or lock contention and implies no retry policy.

### Case 10 — same identity, different content

**OBSERVED:** The request retained the accepted Case 1 response ID and changed
one non-identity answer. The response contained no canonical `outcome`. It
returned spike-only `OPEN_IDENTITY_CONTENT_CONFLICT`, scope
`SPIKE_ONLY_NON_CANONICAL`, one reported physical record for the identity, and
`persistence_effect: none`.

**OPEN:** ADR-0014 does not yet define canonical semantics for the same
`response_id` with non-equivalent content. The experiment detected and refused
the conflict without treating it as `DUPLICATE_ACCEPTED`, `INVALID_REQUEST`, an
update, an overwrite, or a second accepted record.

## Comparative interpretation

**OBSERVED:** Nine cases matched their expected canonical application outcomes.
The tenth produced the deliberately non-canonical OPEN diagnostic. The accepted
identity was reused for Cases 2 and 10, and both responses reported one physical
record with no additional persistence effect. Invalid, unsupported, and
controlled-transient cases all reported no persistence effect.

**INFERRED:** For this tested local-browser, temporary Apps Script, and
disposable-Sheet configuration, the adapter profile demonstrated the complete
experimental pipeline:

```text
text/plain JSON
  -> version gate
  -> limited schema-backed validation
  -> controlled transient gate
  -> ScriptLock-protected identity/hash lookup
  -> conditional disposable append
  -> readable application result
```

It did so without changing the canonical SurveyResponse payload or adding a new
canonical outcome.

## Claim boundary

### OBSERVED

- the exact outcomes, diagnostics, redirect metadata, and client durations in
  the matrix above;
- readable application bodies after the Apps Script ContentService redirect;
- server-reported one-record state for the accepted identity after Cases 1, 2,
  and 10; and
- server-reported absence of persistence effects for Cases 2–10.

### INFERRED

- the bounded adapter profile can distinguish the selected valid, invalid,
  unsupported, duplicate-equivalent, controlled-transient, and identity-content
  conflict cases while preserving canonical SurveyResponse v2;
- the generated canonical-schema snapshot plus limited interpreter was
  sufficient for this controlled fixture matrix; and
- the tested lock-protected identity/hash boundary avoided an additional append
  for the exact repeat and detected non-equivalent content under the same
  identity.

### NOT PROVEN

- direct physical Sheet state after this run, because no independent Sheet
  inspection was supplied with the sanitized browser output;
- execution from the GitHub Pages origin, because this live run used a local
  HTTP harness;
- the temporary deployment's execute-as/access configuration;
- full Draft 2020-12 JSON Schema conformance or behavior for untested schema
  keywords and payload combinations;
- crash safety, exactly-once delivery, durable idempotency, recovery after a
  lost response, multi-deployment consistency, or production concurrency;
- production latency, throughput, quotas, availability, observability,
  privacy lifecycle, retention, deletion, backup, or operational logging;
- production HTTP status mapping, media type, response envelope, CORS/origin
  policy, retry, timeout, authentication, or deployment behavior; or
- continued behavior after Apps Script, browser, schema, taxonomy, deployment,
  or implementation changes.

### NOT SUPPORTED

- selecting Apps Script or Google Sheets as the production adapter/storage;
- treating the experimental response envelope or diagnostic fields as a
  canonical wire contract;
- adding `OPEN_IDENTITY_CONTENT_CONFLICT` as a sixth ADR-0014 outcome;
- treating HTTP 200 alone as application success; or
- starting another spike without first reviewing which ADR-0014 OPEN items this
  accumulated evidence can move to candidate decisions.

### OPEN

- canonical behavior for the same `response_id` with non-equivalent content;
- whether Apps Script and Google Sheets should become the candidate first
  adapter and disposable-to-production storage path;
- all ADR-0014 production choices that this bounded experiment did not prove,
  including deployment, HTTP mapping, retry, timeout, origin policy,
  idempotency lifetime, retention, deletion, and infrastructure logging; and
- whether any further spike is necessary after architecture review.

## Evidence-supported conclusion

The previous synthesis concluded that Apps Script remained a reasonable
candidate for another bounded adapter-profile evaluation. This experiment
performed that evaluation and observed all five existing canonical outcomes,
the selected server-side validation failures, exact-repeat duplicate behavior,
and an explicitly non-canonical OPEN identity/content conflict through a
readable browser response.

This is materially stronger evidence for an architecture review of Apps Script
and Google Sheets as a candidate first adapter. It is not a production adapter
selection, persistence approval, or ADR-0014 acceptance. The next gate is
evidence adjudication against ADR-0014, not an automatic fourth spike.
