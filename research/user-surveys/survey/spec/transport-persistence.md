# Survey transport and persistence contract

**Status:** Proposed
**Contract:** `survey_response/2.0.0`
**Decision:** [ADR-0014](../../../../docs/DECISIONS.md#adr-0014-survey-submission-transport-and-persistence-boundary)

## 1. Status

This is an adapter-neutral architecture and contract proposal. It does not
authorize production transport, persistence, retry, CORS, deployment, or
third-party processing. Every item marked **OPEN** requires explicit approval.

Normative terms apply only to the proposed boundary and existing repository
privacy/schema invariants. They do not convert an OPEN choice into a decision.

## 2. Context

Commit `53b1871` is the baseline UI-validated survey prototype with known
contract-integration gaps. It creates a canonical payload and submits it to a
local demo adapter with no network or persistence. The canonical payload is
owned by [Survey data contract](data-contract.md), its JSON Schema, and shared
taxonomies. Adapters and storage implementations consume that contract.

```text
Survey UI
    -> Canonical SurveyResponse v2
    -> Transport contract
    -> Backend adapter
    -> Storage implementation
```

## 3. Existing client boundary

The checkpoint generates one payload per submit orchestration and calls
`submitSurvey(payload)` once. `crypto.randomUUID()` creates a `response_id`
that is stable for the current page lifecycle. Client validation is a UI
boundary, not an ingestion trust boundary. Known gaps are listed under
Implementation gates and are not changed by this document.

## 4. Decision

The transport boundary accepts exactly one canonical `SurveyResponse v2`
object and produces exactly one canonical semantic outcome. A transport or
adapter MAY encode that operation for its platform, but it MUST NOT redefine
the payload, identifiers, taxonomy, versions, requiredness, or analytical
meaning. Google Apps Script and Google Sheets are candidate implementations,
not contract owners.

## 5. Canonical request contract

- The request value MUST be the exact object defined by
  `survey_response/2.0.0`; no transport wrapper is approved.
- `contract_version` and `survey_version` MUST remain canonical client fields
  and MUST NOT be inferred or overwritten by an adapter.
- An adapter MUST route only explicitly supported versions to a matching
  validator.
- An unsupported version MUST produce `UNSUPPORTED_CONTRACT` and MUST NOT
  produce an accepted persistence side effect.
- Localized labels MUST NOT replace canonical IDs.

HTTP method, media type, redirects, and platform encoding are **OPEN**. If an
adapter cannot transmit the exact canonical object without changing its
semantics, that is an adapter feasibility failure.

## 6. Canonical response and outcome semantics

| Outcome | Meaning |
| --- | --- |
| `ACCEPTED` | The request was validated and persisted once. |
| `DUPLICATE_ACCEPTED` | The same logical submission was already accepted and no additional response record was created. |
| `INVALID_REQUEST` | The request is malformed or fails supported schema, taxonomy, consent, cardinality, exclusivity, conditional-field, or free-text validation. |
| `UNSUPPORTED_CONTRACT` | The declared survey or contract version has no explicitly supported parser/validator. |
| `TEMPORARY_FAILURE` | Acceptance could not be established because processing or storage was temporarily unavailable. |

An outcome MUST NOT expose storage row numbers, stack traces, raw rejected
values, deployment details, secrets, or internal IDs. Validation details
SHOULD use stable paths and codes and MUST NOT echo rejected free text.

Concrete response JSON and HTTP status codes are **OPEN**. The semantic outcome
MUST remain distinguishable independently of HTTP status.

## 7. Validation boundary

Before an accepted persistence side effect, the backend MUST validate:

- object shape and unknown properties;
- supported survey and contract versions;
- required fields and required nullable paths;
- UUID, timestamp, scalar, and array types;
- `consent.research === true`;
- survey enums and version-aligned taxonomy membership;
- array uniqueness, cardinality, and exclusivity;
- conditional `other_*` fields and inactive-field nullability;
- primary-channel membership;
- free-text normalization, length, character, markup, and
  accidental-identifier restrictions.

Client validation MAY improve usability but MUST NOT replace this boundary. A
validator's unsupported formats or conditions MUST NOT be treated as success.

## 8. Idempotency model

`response_id` is the client-generated candidate idempotency key and has no
identity meaning. A backend MUST NOT create a second accepted response record
when it establishes the same logical submission was already accepted.

For any approved retry, the intended invariant is reuse of the exact frozen
payload, including `response_id` and `submitted_at`. These remain **OPEN**:

- idempotency lifetime;
- canonical equality/comparison rules;
- same `response_id` with materially different content;
- whether idempotency evidence survives survey-data deletion;
- whether a post-acceptance edit creates a separately confirmed response.

No idempotency TTL is selected.

## 9. Retry and timeout model

A lost connection or timeout does not establish acceptance or failure; receipt
remains unknown until a canonical outcome is observed. Any future retry of an
indeterminate operation MUST reuse the same frozen logical submission if
idempotent retry is approved.

Automatic retry, retryable failure classes, timeout duration/ownership, manual
retry UX, post-success behavior, duplicate recovery, delay, backoff, and
attempt limits are all **OPEN**. This specification selects no defaults.

## 10. Privacy, logging, and retention

Only a validated canonical response and separately approved server metadata
MAY enter storage. The survey boundary MUST NOT intentionally add or store IP,
User-Agent, referrer, cookies, fingerprints, precise location, advertising or
hidden identifiers, credentials, or deployment secrets as survey data.

Request bodies and accepted or rejected free text MUST NOT be written to
application logs. Errors MUST use coarse outcomes, paths, and stable codes
without respondent content. Raw responses, exports, and runtime storage MUST
remain outside Git.

The following production decisions required by `PRIVACY.md` remain **OPEN**:

- retention for structured responses and restricted free text;
- deletion, correction, withdrawal, and aggregation;
- access roles and storage/data-processing region;
- backup creation, access, retention, and deletion propagation;
- encryption and secret management;
- third-party processor review;
- infrastructure/access logging, including platform IP/User-Agent logs;
- approved server metadata and failure-log fields;
- deletion treatment of idempotency evidence.

## 11. CORS and deployment boundary

Hosting platform, origin model, allowed origins, HTTP mapping, content-type
workarounds, redirects, and deployment visibility are **OPEN**. An adapter
profile MUST document and test actual browser-visible behavior before approval.
If Apps Script cannot provide observable canonical outcomes under the selected
model, that is an adapter feasibility issue and MUST NOT weaken the contract.

## 12. Backend adapter responsibilities

```text
canonical request
    -> version selection and validation
    -> approved idempotency check
    -> storage mapping
    -> persistence
    -> canonical outcome
```

An adapter MUST NOT redefine IDs, localized values, branching, requiredness,
consent, analytical semantics, or versions. It MUST NOT invent answers or
coerce an unsupported contract into a supported one.

## 13. Storage boundary

Storage is replaceable and receives only data that passed validation.
Storage-specific columns, escaping, indexes, locking, transactions,
deduplication, and operational metadata are not part of `SurveyResponse v2`.

Google Sheets is a candidate implementation. Tab names, column order, formula
protection, locking, and server fields require a separate reviewed adapter
profile. Retention, deletion, backup, append-only behavior, and aggregation
remain **OPEN**.

## 14. Failure matrix

| Condition | Outcome | Persistence effect | Retry status |
| --- | --- | --- | --- |
| Valid supported request persisted once | `ACCEPTED` | One accepted record | Complete |
| Already accepted identical logical submission | `DUPLICATE_ACCEPTED` | No additional response record | Complete |
| Malformed shape or failed validation | `INVALID_REQUEST` | None | Correct payload |
| Unsupported survey/contract version | `UNSUPPORTED_CONTRACT` | None | Requires supported contract |
| Temporary validation, idempotency, or storage unavailability | `TEMPORARY_FAILURE` | Acceptance not established | Policy OPEN; frozen payload if retried |
| Timeout or lost response | No observed outcome | Unknown | Policy OPEN; do not claim success/failure |
| Same ID with different content | **OPEN** | Must not overwrite or silently append | **OPEN** |

## 15. Required integration tests

Before adapter approval, tests MUST cover valid locale-equivalent payloads;
unknown and missing fields; versions; all schema/taxonomy/consent/conditional
rules; free-text protection without value echo; accepted and duplicate writes;
the approved same-ID conflict rule; storage injection protection; temporary
failure around possible side effects; approved timeout/retry behavior; response
secrecy; and real-browser method, media-type, redirect, origin, and outcome
behavior. Approved retention, deletion, backup, and logging controls also
require tests.

## 16. Explicit non-goals

This proposal does not implement or authorize Apps Script `doPost`, storage,
production client transport, retry/backoff, CORS, deployment, authentication,
accounts, booking, monitoring subscriptions, notification delivery, analytics,
telemetry, or changes to SurveyResponse v2, schemas, or taxonomy.

## 17. Open decisions

1. First adapter and storage platform.
2. HTTP method, media type, response encoding, and status mapping.
3. Allowed origins, redirects, CORS, and deployment visibility.
4. Google Apps Script deployment/browser feasibility.
5. Timeout duration and ownership.
6. Automatic retry, retryable failures, and manual retry UX.
7. Post-acceptance edit behavior.
8. Idempotency lifetime and same-ID/different-content semantics.
9. Retention and aggregation schedule.
10. Deletion, correction, withdrawal, and idempotency-record treatment.
11. Storage/data region, processor, access, encryption, and secrets.
12. Backup lifecycle and deletion propagation.
13. Infrastructure/access logging and approved error fields.
14. Approved server metadata.
15. Google Sheets mapping, locking, and formula protection if selected.

## 18. Consequences

- Survey semantics remain stable across adapter replacements.
- Adapter constraints surface as feasibility findings, not contract changes.
- Production remains blocked on privacy, lifecycle, deployment, and logging
  decisions.
- Server validation and idempotency need contract-level tests.
- Documentation can advance without authorizing implementation.

## 19. Implementation gates

No production implementation may begin until applicable OPEN decisions are
approved. Before adapter integration, a separately approved change such as
`fix(survey): align web form payload with response contract` must address:

- `consent_research` leaking into `answers`;
- omitted required nullable answer paths;
- incomplete free-text normalization and multiline identifier filtering;
- ignored `showUnless` behavior for `search_duration`;
- reused `response_id` with regenerated `submitted_at` on repeated submits;
- missing interpretation of canonical failure outcomes;
- lack of emitted-payload JSON Schema tests.

Further gates are: update `PRIVACY.md` separately after lifecycle decisions;
prove adapter feasibility in a browser; approve idempotency, retry, timeout,
origin, and outcome mappings; implement authoritative validation and contract
tests; keep secrets/raw data outside Git; and accept ADR-0014 only through an
explicit architecture review.
