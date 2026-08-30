# Multi-Agent Architecture Synthesis — Apps Script Transport and Concurrency Spikes

## 1. Scope

This synthesis evaluates the completed survey transport and disposable
concurrency/persistence research recorded by:

- commit `70eceb6` — `research(survey): record Apps Script transport spike`;
- commit `391d52b` — `research(survey): record Apps Script concurrency spike`;
- `research/user-surveys/survey/spikes/apps-script-transport/2026-08-22-live-browser-evidence.md`;
- `research/user-surveys/survey/spikes/apps-script-transport/2026-08-22-concurrency-persistence-evidence.md`.

It independently evaluates these secondary reviews:

- `research/user-surveys/survey/spikes/apps-script-transport/reviews/grok-architecture-review.md`;
- `research/user-surveys/survey/spikes/apps-script-transport/reviews/claude-architecture-review.md`;
- `research/user-surveys/survey/spikes/apps-script-transport/reviews/gemini-architecture-review.md`.

The reviews are worktree research inputs, not primary evidence and not
canonical specifications. Agreement between reviewers is not treated as
proof.

The canonical baseline was established first from:

- `docs/DECISIONS.md`, ADR-0014;
- `research/user-surveys/survey/spec/transport-persistence.md`;
- `research/user-surveys/survey/spec/data-contract.md`;
- `research/user-surveys/shared/schemas/survey-response.schema.json`;
- the version-aligned canonical taxonomy files under
  `research/user-surveys/shared/taxonomy/`;
- `PRIVACY.md` and `SECURITY.md`;
- current client identity/submission behavior in
  `research/user-surveys/survey/web-form/js/app.js`.

The authority order is canonical contract/ADR, committed empirical evidence,
secondary reviews, then synthesis inference. Source analysis was read-only.
This document is the only artifact created by the synthesis task and does not
change ADR-0014 or authorize implementation.

## 2. Executive Assessment

| Question | Assessment |
| --- | --- |
| Is browser to Apps Script transport technically feasible? | **Yes, in the tested configuration.** Chrome on the tested GitHub Pages origin received readable GET and `text/plain` POST acknowledgements after the ContentService redirect. This is not a universal CORS guarantee. |
| Is locked duplicate-check plus append technically feasible? | **Yes, for the tested disposable path.** The locked shared-ID run left one physical row; the unlocked control left seven. |
| Is Apps Script justified as a candidate adapter? | **Yes, as a candidate for a further bounded adapter-profile evaluation.** This is a reasonable design inference, not selection. |
| Is Apps Script selected as the production adapter? | **No.** ADR-0014 is Proposed and adapter selection remains OPEN. |
| Is Google Sheets selected as production persistence? | **No.** The Sheet was disposable and lifecycle, security, mapping, durability, and scale were not approved. |
| Is the system safe for public deployment? | **No evidence supports that conclusion.** Deployment access, origin controls, privacy lifecycle, logging, abuse handling, and operational policy remain unresolved. |
| Is automatic retry justified? | **No.** Retry classes, timeout ownership, backoff, attempt limits, equality rules, and uncertain-outcome handling remain OPEN and were not tested. |

The appropriate overall assessment is: transport and one concurrency mechanism
are technically feasible; an adapter design is partially supported as a
candidate; no production or public-deployment decision is justified.

## 3. Canonical Baseline

### ADR and ownership

ADR-0014 is **Proposed**, not Accepted (`docs/DECISIONS.md`, “ADR-0014:
Survey Submission Transport and Persistence Boundary”). Its dependency
direction is:

```text
Survey UI
    -> Canonical SurveyResponse v2
    -> Adapter-neutral submission contract
    -> Backend adapter
    -> Storage implementation
```

`research/user-surveys/survey/spec/data-contract.md` owns the canonical
`survey_response/2.0.0` object, field meaning, versions, schema relationship,
and taxonomy references. Apps Script and Sheets are candidate consumers and
must not redefine that contract.

### Identity and idempotency

`data-contract.md`, “Submission envelope,” defines `response_id` as a
client-generated cryptographically secure UUID v4 with no identity meaning
and calls it the idempotency key. ADR-0014 and
`transport-persistence.md`, “Idempotency model,” more cautiously call it the
client-generated **candidate idempotency key** because its production
lifetime and conflict policy are not approved.

The repository therefore already owns the idempotency identity: `response_id`.
A new `idempotency_key` is neither required nor authorized by current evidence.
Still OPEN are lifetime/TTL, canonical equality, same-ID/different-content,
post-acceptance edits, and whether deduplication evidence survives deletion.

For an approved retry, `transport-persistence.md` states the intended invariant
of reusing the exact frozen payload, including `response_id` and
`submitted_at`. Current `web-form/js/app.js` keeps `response_id` in page state
but constructs a new `submitted_at` inside each submit handler. The spec already
records this as an integration prerequisite; it is not evidence that a second
identity field is needed.

### Canonical outcomes

The only five adapter-neutral outcomes are:

- `ACCEPTED`;
- `DUPLICATE_ACCEPTED`;
- `INVALID_REQUEST`;
- `UNSUPPORTED_CONTRACT`;
- `TEMPORARY_FAILURE`.

They are defined in ADR-0014 and `transport-persistence.md`, “Canonical
response and outcome semantics.” Experimental statuses such as
`SUCCESS_ROW_WRITTEN`, `DUPLICATE_DETECTED`, and `LOCK_REJECTED` are probe
instrumentation and are not public contract values.

An already accepted identical logical submission maps to
`DUPLICATE_ACCEPTED` with no additional accepted record. However, equality
rules and the same-ID/different-content case remain OPEN. A timeout or lost
response yields no observed outcome and unknown acceptance, not an automatic
`TEMPORARY_FAILURE`.

### Validation, transport, and lifecycle

The backend must independently validate supported versions, object shape,
required nullable paths, consent, taxonomy membership, cardinality,
exclusivity, conditionals, and free-text restrictions before an accepted
persistence side effect (`transport-persistence.md`, “Validation boundary”).
Client validation is not an ingestion trust boundary.

The following remain OPEN in `transport-persistence.md`, “Open decisions”:

- first adapter and storage platform;
- method, media type, response encoding, and HTTP status mapping;
- origin model, redirects, CORS, deployment visibility, and access settings;
- lock API, granularity, timeout, and Sheets mapping if Sheets is selected;
- automatic/manual retry, retryable classes, delay/backoff, and attempt limits;
- idempotency lifetime, equality/conflict rules, and edit behavior;
- retention, deletion, withdrawal, aggregation, backups, and deduplication
  evidence lifecycle;
- processor/region, access, encryption, secrets, approved server metadata,
  infrastructure logging, and permitted error fields.

`PRIVACY.md`, “Data storage and retention,” requires these lifecycle choices
before production but selects no duration. `transport-persistence.md`,
“Privacy, logging, and retention,” prohibits intentional collection of IP,
User-Agent, referrer, cookies, fingerprints, precise location, advertising or
hidden identifiers as survey data and prohibits request bodies or free text
in application logs. `SECURITY.md` remains Draft and states that no production
deployment exists.

## 4. What the Two Spikes Establish

### Transport spike

**OBSERVED:** In the 2026-08-22 tested Chrome, GitHub Pages origin, and
temporary Apps Script deployment configuration:

- a `POST` using `mode: "cors"`, `Content-Type: text/plain`, and a JSON-encoded
  probe body reached `doPost(e)` and was parsed;
- the observed route included `script.google.com` HTTP 302 followed by a final
  `script.googleusercontent.com` HTTP 200 ContentService response;
- the browser received `response.type = "cors"`, `redirected = true`, and a
  readable application acknowledgement containing the probe request ID;
- GET independently returned a readable acknowledgement;
- `no-cors` returned an opaque status-0 response and proved only a dispatch
  attempt;
- both `RECEIVED` and `INVALID_PROBE` were observed with final HTTP 200, so
  HTTP 200 alone did not establish application success.

**INFERRED:** An intermediate proxy was not required solely to obtain a
readable browser-to-Apps-Script acknowledgement in that configuration.

Primary locator: `2026-08-22-live-browser-evidence.md`, “Valid POST
observation,” “Valid GET observation,” “`no-cors` POST observation,” and
“Invalid-probe observations.”

### Concurrency/persistence spike

The disposable concurrency implementation and Sheet were not retained. The
committed report is therefore trusted first-party experiment evidence, but the
critical-section implementation cannot be independently reproduced or audited
from repository code alone.

**Phase 0 — OBSERVED:** One post-burst locked request completed in 1814.5 ms,
reported 67 ms lock wait, and returned HTTP 200 with a readable
`SUCCESS_ROW_WRITTEN` probe response. This is one observation, not a latency
floor.

**Phase 1 — OBSERVED:** A 20-request locked unique-ID burst with 50 ms stagger
and `tryLock(10000)` produced 11 `SUCCESS_ROW_WRITTEN` and 9
`LOCK_REJECTED` responses over 12335.931884765625 ms. Completion was not in
request-index order. Rejections appeared around the configured acquisition
timeout; they were not HTTP overload evidence.

**Phase 2 — OBSERVED:** A 20-request locked shared-`probe_id` burst produced:

- 1 `SUCCESS_ROW_WRITTEN`;
- 13 `DUPLICATE_DETECTED`;
- 6 `LOCK_REJECTED`;
- one physical row for the shared ID after Sheet inspection;
- 12510 ms total duration.

**Phase 3 — OBSERVED:** The unlocked 20-request shared-ID negative control
produced:

- 7 `SUCCESS_ROW_WRITTEN`;
- 13 `DUPLICATE_DETECTED`;
- seven physical rows for the shared ID;
- no lock waiting;
- 3537.72705078125 ms total duration.

**INFERRED:** ScriptLock serialized entry to the tested protected section.
Keeping duplicate lookup and append inside that section preserved the tested
single-row invariant, while the unlocked path exposed a duplicate-write race.
Contention materially contributed to client-visible latency.

Primary locator: `2026-08-22-concurrency-persistence-evidence.md`, “Phase 0”
through “Phase 3,” “Controlled comparison,” and “Latency evidence.”

The earlier direct-POST HTTP 403 observations are a separate transport
boundary. Their cause is NOT PROVEN and they must not be equated with the
application-level `LOCK_REJECTED` probe result.

## 5. What the Two Spikes Do Not Establish

The spikes do not establish:

- Apps Script or Sheets selection, production readiness, or public-deployment
  safety;
- canonical `SurveyResponse v2` ingestion, authoritative server validation,
  or emission of the five canonical outcomes;
- exactly-once delivery, transaction semantics, crash-safe idempotency,
  idempotency lifetime, equality rules, or same-ID/different-content behavior;
- a production lock API, lock granularity, timeout, retry class, retry delay,
  backoff algorithm, or attempt limit;
- universal CORS readability, allowed-origin enforcement, deployment access
  model, authentication, or abuse controls;
- production retention, deletion, withdrawal, logging, backup, encryption,
  processor, data region, or access controls;
- a stable latency baseline, p95/p99, cold-start behavior, FIFO/fairness,
  maximum concurrency, request rate, row-count threshold, throughput, or
  migration threshold;
- behavior across other browsers, origins, accounts, deployments, code
  revisions, configurations, or platform changes.

The tested 20-request bursts are research stimuli, not expected survey-traffic
models.

## 6. Review-by-Review Assessment

### Grok

Grok is the most conservative review. Its strongest evidence-backed findings
are the bounded readable transport path, HTTP-200/application-result
distinction, locked/unlocked row comparison, increased contention latency, and
preservation of `response_id` and the five outcomes. It appropriately rejects
production selection, fixed timeout, automatic retry, backoff, scale
thresholds, and lifecycle decisions.

Its suggestion to evaluate canonical validation and outcome emission next is
a useful design inference, not a decision. Its label “official doc” for the
repository data contract should instead be
`SUPPORTED_BY_CANONICAL_SPEC`.

### Claude

Claude most clearly separates technical feasibility, candidate status, and
public-deployment safety. It usefully identifies that the disposable
concurrency implementation was not retained, limits ScriptLock support to the
tested hazard, rejects a new identity field and quantitative thresholds, and
decomposes uncertain retry cases.

Its assertion that the locked/unlocked run changed exactly one variable is
stronger than the retained artifacts can independently verify. Its proposed
adapter vertical slice and provisional `tryLock` use are design proposals, not
evidence-backed decisions. Its table also treats same-ID/same-content as
wholly unaddressed: the spike did not test canonical payload equality, but the
canonical contract already assigns identical logical resubmission to
`DUPLICATE_ACCEPTED`; only equality rules remain OPEN.

Claude's client note is current: `app.js` retains `response_id` but regenerates
`submitted_at` for each submit invocation. This remains an integration gate,
not a reason to change the schema.

### Gemini

Gemini correctly records the basic readable transport evidence, 1-versus-7
physical-row comparison, observed lock contention, lack of retry testing, and
unresolved privacy/security lifecycle.

It materially overreaches elsewhere:

- a new `idempotency_key` contradicts `data-contract.md`, which already assigns
  that role to `response_id`;
- experimental statuses proposed as canonical response values contradict
  ADR-0014's five outcomes;
- `tryLock(5000)`, 5–10 requests/second, and fewer than 10,000 rows are
  unsupported quantitative choices;
- “low-volume” production suitability and Sheets scale are untested;
- public “Anyone” deployment and origin-enforcement assertions are unsupported
  by the retained experiment, whose deployment settings were not recorded;
- “contention latency floor” contradicts the primary report's explicit
  non-claim;
- 302/307 generalization exceeds the observed 302 route;
- same-ID/same-content was not empirically tested at canonical payload-equality
  level.

Gemini's proposed schema and ADR update sequence must therefore be rejected.

## 7. Cross-Review Consensus

All three reviews converge on the following conclusions, and the primary
repository evidence independently supports them:

- a readable browser-to-Apps-Script acknowledgement was feasible in the one
  tested configuration;
- `text/plain` JSON worked as an adapter-specific encoding;
- `no-cors` was opaque and did not prove receipt;
- HTTP 200 alone did not distinguish the observed application outcomes;
- the locked shared-ID run left one row and the unlocked control left seven;
- lock contention materially affected observed latency;
- 10 seconds was an experiment parameter, not a production timeout;
- retry/backoff were untested and should not be selected from these spikes;
- origins, deployment, security, privacy, retention, and deletion remain OPEN;
- public production readiness was not established.

Their varying consensus that Apps Script and Sheets merit further
consideration supports only a candidate-design inference. Consensus does not
select either component.

## 8. Cross-Review Disagreements

| Disagreement | Resolution |
| --- | --- |
| New identity field | Grok and Claude preserve `response_id`; Gemini proposes `idempotency_key`. Canonical `data-contract.md` resolves this against Gemini: `response_id` already owns the role. |
| Apps Script/Sheets readiness | Grok says not yet justified, Claude says conditional prototype candidates, Gemini implies low-volume production candidacy. Evidence supports technical feasibility and candidate consideration only. |
| Lock mandate | Gemini generalizes; Claude limits it to the tested hazard; Grok calls it a possible boundary. Evidence supports “required by the tested design to preserve its single-row invariant,” not universal necessity. |
| `tryLock` selection | Grok keeps it experimental, Claude suggests provisional use, Gemini later chooses 5 seconds. No `waitLock` comparison or timeout sensitivity experiment resolves this. OPEN. |
| Same-ID/same-content | Gemini treats it as empirically proven; Claude calls it open. Canonically, an identical logical submission maps to `DUPLICATE_ACCEPTED`, but equality rules and the spike's relationship to canonical content remain OPEN. |
| Next step | Grok favors canonical validation/outcome evidence, Claude a gated adapter prototype, Gemini schema invention and ADR promotion. Only the first can be scoped without changing an approved contract or selecting production infrastructure. |

## 9. Claim Adjudication Matrix

Abbreviations in reviewer columns: **Y** endorses, **P** partially or
conditionally endorses, **N** rejects, and **O** leaves open.

| Claim | Grok | Claude | Gemini | Primary evidence | Canonical source | Synthesis classification | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Apps Script is ready as first production adapter | N | P | P/Y | Bounded transport and disposable concurrency only | ADR-0014 Proposed; first adapter OPEN | `PREMATURE_OR_UNSUPPORTED` | Technically feasible candidate; not selected or production-ready. |
| 2. Sheets is justified as production persistence | N | P | Y for low scale | Disposable Sheet only | Storage platform and lifecycle OPEN | `PREMATURE_OR_UNSUPPORTED` | Candidate consideration only. |
| 3. LockService is mandatory | P, tested design | P, tested hazard | Y | Locked 1 row versus unlocked 7 | Locking remains adapter-specific/OPEN | `SUPPORTED_BY_OBSERVATION` bounded; universal claim unsupported | Required by tested design, not universally mandatory. |
| 4. ScriptLock is the correct granularity | O | P | P | ScriptLock was the only tested granularity | Lock granularity OPEN | `REQUIRES_ADDITIONAL_EVIDENCE` | Worked in test; “correct” is undecided. |
| 5. `tryLock` is preferable to `waitLock` | O | P provisionally | O | Only `tryLock` tested | Timeout/lock policy OPEN | `REQUIRES_ADDITIONAL_EVIDENCE` | No comparative basis. |
| 6. 10 seconds is an appropriate production timeout | N | N | N/benchmark | 10 seconds was configured; rejections clustered near it | Timeout OPEN | `PREMATURE_OR_UNSUPPORTED` | Experiment parameter only. |
| 7. 5 seconds is an appropriate production timeout | N | N | Y in proposed slice | Not tested | Timeout OPEN | `PREMATURE_OR_UNSUPPORTED` | Unsupported number. |
| 8. Automatic retries should be implemented | N | N | N for now | No retry experiment | Retry policy OPEN | `PREMATURE_OR_UNSUPPORTED` + `SUPPORTED_BY_CANONICAL_SPEC` as OPEN | Do not implement. |
| 9. Exponential backoff with jitter should be implemented | N | N | P as candidate | Not tested | Backoff and delay OPEN | `PREMATURE_OR_UNSUPPORTED` | Generic pattern, not project decision. |
| 10. `LOCK_REJECTED` is safe to retry | N/O | Conditional inference | O | Probe failed to acquire lock before its tested critical section | Probe status is non-canonical; retry mapping OPEN | `REQUIRES_ADDITIONAL_EVIDENCE` | No production retry-safety conclusion. |
| 11. Add a new `idempotency_key` | N | N | Y | Probe used `probe_id`, not canonical schema | `response_id` is the idempotency key | `CONTRADICTS_CANONICAL_SOURCE` | Reject. |
| 12. `response_id` is insufficient | N | N | Y | Spikes did not test insufficiency | Canonical contract assigns this role to `response_id` | `PREMATURE_OR_UNSUPPORTED`; schema-change form contradicts canonical source | No evidence of insufficiency. |
| 13. Same-ID/same-content behavior is already defined | O | O | Y | Same `probe_id` test did not establish canonical equality | Identical logical submission maps to `DUPLICATE_ACCEPTED`; equality rules OPEN | Partial `SUPPORTED_BY_CANONICAL_SPEC` | Outcome is defined; comparison rule is not. |
| 14. Same-ID/different-content behavior is already defined | N/O | O | O, proposes rejection | Not tested | Explicitly OPEN | `CONTRADICTS_CANONICAL_SOURCE` if claimed defined | Must remain OPEN. |
| 15. `text/plain` JSON should become canonical transport | P adapter-only | P adapter-only | Y for adapter | Worked in one browser/deployment configuration | Method/media type OPEN | Observed feasibility; canonicalization `PREMATURE_OR_UNSUPPORTED` | Candidate adapter encoding only. |
| 16. Readable CORS is guaranteed for production | N | N | Overgeneralizes | One Chrome/origin/deployment; access settings unretained | CORS/deployment OPEN | `PREMATURE_OR_UNSUPPORTED` | Bounded observation only. |
| 17. Allowed Origins can/should be enforced by Apps Script | O | O | Makes platform assertions | Not tested | Origin/access model OPEN | `REQUIRES_ADDITIONAL_EVIDENCE` | No established enforcement property or choice. |
| 18. A safe threshold such as fewer than 10,000 rows exists | N | N | Y | No volume/row-scale experiment | No threshold selected | `PREMATURE_OR_UNSUPPORTED` | Reject quantitative threshold. |
| 19. HTTP 200 represents transport success | N as app success | N as app success | Says body required | Final HTTP 200 was readable for both valid and invalid probes | HTTP mapping OPEN | `SUPPORTED_BY_OBSERVATION` as completion only; application-success claim contradicted | Parse canonical outcome; do not infer acceptance. |
| 20. Locked lookup plus append preserved the single-row invariant | Y bounded | Y bounded | Y | Locked: 1 row; unlocked: 7 rows | Does not select production storage/idempotency | `SUPPORTED_BY_OBSERVATION` + bounded inference | Supported for tested path and run. |

## 10. ADR-0014 Decision Readiness

### Candidate decisions now evidence-supported

These facts are ready to be recorded as feasibility inputs, not accepted
production decisions:

- one Apps Script adapter profile can carry a readable application body from
  the tested GitHub Pages browser path using `text/plain` JSON;
- in that profile, the application body—not HTTP 200 alone—must distinguish
  semantic results;
- ScriptLock around the tested duplicate lookup and append preserved the
  single-row invariant under the tested contention;
- lock contention and configured-timeout rejection are material adapter design
  constraints.

### Decisions requiring explicit architecture choice

- whether Apps Script and/or Sheets becomes the first reviewed adapter profile;
- whether the tested media type becomes part of that adapter profile;
- canonical response encoding and mapping from internal conditions to the five
  outcomes;
- lock granularity/API, conflict handling, and storage mapping;
- equality and same-ID/different-content semantics.

### Decisions requiring another spike

- authoritative `SurveyResponse v2` validation and observable canonical
  outcomes through the real browser redirect path;
- selected deployment access/execute-as settings and browser-visible origin,
  redirect, and response behavior;
- failure injection around commit-versus-lost-acknowledgement if retry is later
  considered;
- `tryLock` versus `waitLock` only if both remain actual candidates.

### Decisions that must remain OPEN

- production adapter/storage selection;
- automatic retry, retryable classes, timeout, backoff, and attempt limits;
- idempotency lifetime, deduplication-record deletion, and post-acceptance edits;
- retention, deletion, correction, withdrawal, aggregation, and backups;
- deployment visibility, origins, access control, abuse controls, logging,
  processor/region, encryption, secrets, and approved metadata;
- scale, throughput, latency SLOs, and migration thresholds;
- public-deployment approval.

## 11. Retry and Idempotency Assessment

### Existing identity

`response_id` already carries canonical idempotency identity. The unresolved
work is its operational policy, not an absent key. The client must satisfy the
frozen-payload invariant before retry can be evaluated; currently
`submitted_at` is regenerated on each submit invocation.

### Definite lock rejection

The probe's `LOCK_REJECTED` meant failure to acquire the experimental lock
within its configured timeout and occurred before its protected probe write.
That makes “potentially transient” a reasonable design inference. It does not
make the probe status a canonical outcome or prove automatic retry safety.
The adapter would first need an approved mapping, idempotency policy, attempt
budget, and contention analysis.

### Network uncertainty

A client-visible network failure generally does not establish whether the
backend received or committed the request. `transport-persistence.md`, “Retry
and timeout model,” correctly leaves receipt unknown. A claim that failure
occurred “before receipt” is safe only when non-receipt is independently
established, not inferred from the browser error alone.

### Commit followed by lost acknowledgement

This is the core reason an approved retry must reuse the same frozen payload.
A conforming adapter should return `DUPLICATE_ACCEPTED` when it establishes
that the identical logical submission was already accepted without creating a
second accepted record. The spike supports one locked lookup/append mechanism,
but did not inject a lost acknowledgement or prove crash safety.

### Same ID cases

- Same ID and identical logical submission: canonical result is
  `DUPLICATE_ACCEPTED`, but canonical equality/comparison rules remain OPEN.
- Same ID and different content: explicitly OPEN; must not overwrite or
  silently append according to the failure matrix.

### Backoff

Exponential backoff with jitter is a general distributed-systems pattern, not
an evidence-backed project decision. The spikes did not measure retry success,
retry storms, delay schedules, or attempt limits. It must not be implemented
until failure-to-outcome mapping and retry eligibility are approved and then
tested.

## 12. Security / Privacy / Lifecycle Gaps

Repository-supported gaps that block public production include:

- the temporary deployment's access and execute-as settings were not retained;
- allowed-origin behavior and whether any origin control is reliable in the
  selected deployment are untested;
- no public access, authentication, abuse/rate-control, or deployment-visibility
  model is approved;
- no production retention, aggregation, deletion, correction, withdrawal, or
  backup lifecycle is approved;
- no processor/data region, access-role, encryption, or secret-management
  profile is approved;
- infrastructure/access logging, including unavoidable platform IP or
  User-Agent processing, is unreviewed;
- request bodies and free text must not enter application logs, but platform
  logging behavior has not been verified;
- the disposable Sheet does not demonstrate formula protection, production
  mapping, access controls, durability, deletion propagation, or privacy rights.

The transport observation does not prove that Apps Script can enforce Allowed
Origins or that a public endpoint is safe. Those are separate platform and
architecture questions.

## 13. Minimum Justified Next Step

The smallest justified next gate is an **adapter-profile contract-validation
spike**, still isolated and non-production:

1. Keep `SurveyResponse v2`, `response_id`, taxonomies, and the five outcomes
   unchanged.
2. Use sanitized canonical fixtures to exercise authoritative server-side
   schema/version/consent/taxonomy/conditional/free-text validation.
3. Return a readable representation of each canonical outcome through the
   candidate browser redirect path, without treating HTTP 200 as the outcome.
4. Record the exact test deployment access and execute-as configuration and
   re-evaluate browser-visible origin/redirect behavior.
5. Include no real responses and no durable production storage. If a storage
   stub is necessary to observe `ACCEPTED`/`DUPLICATE_ACCEPTED`, keep it
   disposable and explicitly outside production lifecycle claims.

This gate should not implement automatic retry, backoff, a new idempotency
field, a production timeout, retention/deletion, public deployment, production
Sheets persistence, authentication, or scale thresholds. Adapter/storage
selection and ADR acceptance remain separate architecture decisions.

## 14. Final Synthesis

- **FEASIBILITY ESTABLISHED:** readable browser-to-Apps-Script acknowledgement
  and a locked single-row invariant were observed in bounded configurations.
- **CANDIDATE DESIGN PARTIALLY SUPPORTED:** Apps Script, `text/plain` JSON, and
  a ScriptLock-protected lookup/append are reasonable adapter-profile
  candidates, not universal requirements.
- **PRODUCTION DECISION NOT YET JUSTIFIED:** ADR-0014 is Proposed; canonical
  validation/outcomes, lifecycle, retry, deployment, and operational policy
  are unresolved.
- **PUBLIC DEPLOYMENT NOT YET CLEARED:** security, privacy, origin/access,
  logging, retention, deletion, and abuse boundaries lack approved evidence.

No reviewer consensus overrides these source-backed boundaries.
