# Apps Script adapter-profile contract-validation spike

**Status:** completed bounded research experiment; live evidence recorded

## Research question

Can a bounded Google Apps Script adapter profile receive one canonical
`survey_response/2.0.0`, validate it server-side, prevent invalid input from
reaching disposable storage, use canonical `response_id` for the tested
duplicate boundary, and return a readable canonical semantic outcome through
the previously observed browser transport without changing SurveyResponse v2?

This directory implements the manual experiment only. It is not a production
adapter, production persistence, an ADR-0014 decision, a final wire protocol,
or a production Google Sheets design. Use synthetic fixtures only.

## Evidence lineage

- Spike 1 (`70eceb6`) observed a readable GitHub Pages to Apps Script
  `text/plain` POST acknowledgement after the ContentService redirect.
- Spike 2 (`391d52b`) observed that a ScriptLock-protected duplicate lookup and
  conditional append preserved the tested single-row invariant, while the
  unlocked control produced duplicate rows.
- The synthesis (`ab0153e`) concluded that a canonical validation/outcome
  adapter-profile experiment is the smallest justified next evidence gate.

Those findings are bounded. This spike does not turn them into production
choices.

## Files

- `Code.gs` — experimental handler, schema-subset interpreter, ScriptLock
  boundary, and two-column disposable storage adapter.
- `ContractSnapshot.gs` — generated deployable snapshot of the committed
  canonical JSON Schema. Do not edit it manually.
- `fixtures/valid-survey-response.json` — synthetic known-good canonical fixture.
- `harness/` — manual GitHub Pages matrix UI.
- `2026-08-29-live-contract-validation-evidence.md` — sanitized live matrix
  observations and bounded interpretation.
- `tools/build_contract_snapshot.py` — regenerates the schema snapshot and
  verifies taxonomy enum alignment.
- `tests/` — local canonical-schema, adapter behavior, syntax, and browser smoke
  checks.

## Manual matrix

| Case | Controlled input | Expected observation | Disposable write |
| ---: | --- | --- | ---: |
| 1 | Valid canonical response | `ACCEPTED` | One |
| 2 | Exact repeat of the in-memory Case 1 payload | `DUPLICATE_ACCEPTED` | None |
| 3 | Malformed JSON | `INVALID_REQUEST` | None |
| 4 | Missing required nullable `answers.appointment_urgency` | `INVALID_REQUEST` | None |
| 5 | Invalid `response_id` UUID | `INVALID_REQUEST` | None |
| 6 | Unknown `centre_ids` taxonomy value | `INVALID_REQUEST` | None |
| 7 | String instead of array for `problem_category_ids` | `INVALID_REQUEST` | None |
| 8 | Unsupported string `contract_version` | `UNSUPPORTED_CONTRACT` | None |
| 9 | Valid body plus out-of-band spike transient control | `TEMPORARY_FAILURE` | None |
| 10 | Case 1 `response_id` with one changed answer | `OPEN_IDENTITY_CONTENT_CONFLICT` spike-only result | None |

Case 10 intentionally has no `outcome`. Same identity with different content
is OPEN in `survey/spec/transport-persistence.md`. The adapter detects the
condition, refuses to overwrite or append, and returns the non-canonical
`spike_result: OPEN_IDENTITY_CONTENT_CONFLICT`. This result must not be added to
ADR-0014 or treated as a sixth canonical outcome.

## Validation strategy

The build tool embeds the actual committed
`shared/schemas/survey-response.schema.json` into `ContractSnapshot.gs`. It
also compares the schema's centre, problem-category, and notification-channel
enums with all three canonical taxonomy artifacts. This avoids maintaining a
second handwritten taxonomy registry in `Code.gs`.

`Code.gs` interprets only the JSON Schema keywords used by the current
canonical schema:

- local `$ref`, `type`, `const`, `enum`, `pattern`, and the used formats;
- `required`, `properties`, and `additionalProperties: false`;
- string/number/array bounds, `uniqueItems`, `items`, and `contains`;
- `anyOf`, `allOf`, and `if`/`then`/`else`.

This is not a general Draft 2020-12 validator and must not be represented as
one. In particular, it does not implement arbitrary remote references,
unevaluated keywords, annotation collection, full Unicode code-point length
semantics, or keywords absent from the current schema. Local tests validate
the fixture and controlled negative mutations with PowerShell `Test-Json`
against the real canonical Draft 2020-12 schema, then independently verify the
spike interpreter's outcome classification. A stale generated snapshot fails
the local check.

Production taxonomy synchronization remains unsolved. Regenerate and review
the snapshot before every experiment; any canonical schema/taxonomy drift is a
stop condition.

## Experimental response envelope

Successful matrix responses use the five existing canonical outcome names in
an experimental envelope such as:

```json
{
  "spike_version": "3.0.0",
  "outcome": "ACCEPTED",
  "envelope_status": "EXPERIMENTAL_NOT_A_PRODUCTION_CONTRACT",
  "diagnostic": {
    "code": "validated_identity_hash_recorded"
  }
}
```

The surrounding JSON, diagnostic codes, and HTTP behavior are not a production
response contract. HTTP mapping remains OPEN. Diagnostics contain stable codes
and paths only; rejected values and full payloads are not returned or logged.

## Disposable persistence and locking

The Sheet stores only:

```text
response_id | payload_sha256
```

It does not store the synthetic SurveyResponse body. SHA-256 is calculated over
a recursively key-sorted JSON representation, so Case 2 preserves the exact
Case 1 fixture while the backend also tolerates object-key ordering differences.
Arrays retain their canonical order.

Duplicate lookup and conditional append run inside
`LockService.getScriptLock()`, reusing only the bounded Spike 2 lesson. The
`EXPERIMENTAL_LOCK_TIMEOUT_MS = 3000` value is an arbitrary bounded fixture
parameter required to execute this experiment. It is not a production timeout
recommendation and does not select `tryLock` over `waitLock` as architecture.
Failure to acquire the experimental lock maps to `TEMPORARY_FAILURE` for this
matrix only.

Case 9 is deterministic: the harness adds
`spike_control=temporary_failure` to the endpoint query while sending an
unchanged valid SurveyResponse body. The handler returns `TEMPORARY_FAILURE`
before lock acquisition or persistence. The control is not a SurveyResponse
field and implies no retry policy.

## Temporary Apps Script setup

1. Create a new disposable Google Sheet containing no real survey data.
2. Create a standalone temporary Apps Script project.
3. Add `ContractSnapshot.gs` and `Code.gs` to that project.
4. In Apps Script Project Settings, add the Script Property
   `SPIKE_SPREADSHEET_ID` with the disposable Sheet ID. Never commit or paste
   that value into evidence.
5. Deploy a temporary Web App using deliberate test-only execute-as and access
   settings. Record those settings separately for later sanitized evidence.
6. Do not commit the deployment endpoint.

The script creates a tab named `ContractValidationSpike` with the two headers
shown above. It adds no analytics, archive, retention job, deletion workflow,
telemetry, retry, or operational logging.

## Harness setup

The spike Pages workflow publishes only `harness/index.html`,
`harness/probe.js`, and the synthetic fixture under the Spike 3 path. It does
not publish Apps Script code, tests, specifications, reviews, or unrelated
research.

Open the deployed `apps-script-contract-validation/harness/` path, paste the
temporary endpoint into the non-persistent input, and trigger each case
manually. The harness never sends an adapter request on page load and uses no
cookies, localStorage, sessionStorage, IndexedDB, analytics, timeout, retry,
backoff, or automatic matrix execution.

Case 1 creates a fresh UUID and timestamp once. After it returns `ACCEPTED`,
Cases 2 and 10 become enabled. Case 2 reuses the exact stored in-memory object,
including `response_id` and `submitted_at`. Case 10 clones that object,
preserves `response_id`, and changes only `answers.early_testing_interest`.
Reloading or clearing results discards the in-memory fixture.

Use **Copy sanitized results** after the run. The output includes case ID/name,
expected and observed result, HTTP status, response type, redirect flag,
sanitized final host/path marker, duration, synthetic `response_id`, expected
write effect, and `PASS`/`FAIL`/`OPEN`/`NETWORK_ERROR`. It excludes the endpoint,
complete redirect URL, Sheet ID, and full request body.

## Resetting disposable state

For a clean rerun, delete all data rows below the two-column header in the
`ContractValidationSpike` tab, or delete that tab and allow the script to
recreate it. Then reload the harness so it creates a new in-memory Case 1
identity. Never reuse the Sheet for real responses.

## Intentional omissions

- no automatic retry, exponential backoff, jitter, or client timeout;
- no authentication or allowed-origin decision;
- no production storage mapping, retention, deletion, or backup behavior;
- no scale, throughput, or latency claim;
- no changes to SurveyResponse, schema, taxonomy, ADR-0014, or canonical
  outcomes;
- no production evidence or decision beyond the bounded live report.

## Local verification

From the repository root:

```powershell
python research/user-surveys/survey/spikes/apps-script-contract-validation/tools/build_contract_snapshot.py --check
node research/user-surveys/survey/spikes/apps-script-contract-validation/tests/contract_validation_test.js
python -m unittest research/user-surveys/survey/spikes/apps-script-contract-validation/tests/spike_test.py -v
node --check research/user-surveys/survey/spikes/apps-script-contract-validation/harness/probe.js
```
