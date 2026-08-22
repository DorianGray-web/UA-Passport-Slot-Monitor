# Independent Read-Only Architecture & Evidence Review

### Target Branch:

 spike/survey-pages-transport

### Primary Commits:

 391d52b (concurrency/persistence spike), 70eceb6 (transport spike)

### Baseline Decision Context

 ADR-0014 (docs/DECISIONS.md)

## Executive Assessment

- Technically Implementable: YES.
  The combined evidence proves that a browser client can dispatch payloads via text/plain cross-origin fetch to Google Apps Script (GAS), follow Google's redirect to script.googleusercontent.com, parse the JSON outcome from a 200 OK response body, and execute a synchronized duplicate lookup -> conditional append against Google Sheets using LockService.getScriptLock().

- Justified Production Candidate: PARTIALLY. GAS and Google Sheets are justified as a candidate first adapter for low-volume, non-critical survey collection. However, critical gaps around retry safety, client idempotency keys, lock timeout strategy, and Same-ID/Different-Content semantics remain unverified.

- Safe for Public Deployment: NO. Unresolved security, privacy, and transport controls render a public deployment premature.

   Specifically:

  1. The execution URL requires Anyone execution context, leaving it open to unauthenticated public submission without origin enforcement at the platform layer.
  2. The application lacks an explicit client-generated idempotency key, making automated retry mechanisms dangerous.
  3. No retention, deletion, or privacy/data region guarantees exist for responses containing potential PII/user telemetry.

## Evidence Established by Spike 1 (Transport Spike — Commit 70eceb6)

   Derived from 2026-08-22-live-browser-evidence.md and transport harness.
     * Cross-Origin Browser Redirection Flow: Confirmed that fetch() from GitHub Pages to the `script.google.com` host at the `/macros/s/<deployment>/exec` path pattern triggers a 302/307 redirect to the `script.googleusercontent.com` host, which can be followed seamlessly by standard browser fetch options (redirect: 'follow').
     * Readable Responses via text/plain CORS: A POST payload sent with Content-Type: text/plain avoids CORS preflight triggers while allowing GAS doPost(e) to ingest e.postData.contents. The script returns ContentService.createTextOutput(...), allowing the client browser to read the JSON response body across origins.
     * no-cors Insufficiency: Opaque responses produced via no-cors establish dispatch confirmation at the network transport layer but hide application-level status, making error handling and receipt verification impossible.
     * HTTP 200 vs. Application Success: Application errors in GAS return HTTP 200 OK with JSON payloads indicating error states (e.g., { status: "ERROR", message: "..." }). The client must parse the response body; relying on HTTP status codes alone is a critical failure mode.

## Evidence Established by Spike 2 (Concurrency Spike — Commit 391d52b)

    Derived from 2026-08-22-concurrency-persistence-evidence.md and concurrency harness.

     * UNLOCKED Race Condition (Negative Control): Executing 20 concurrent requests with duplicate IDs against an unprotected Sheet resulted in 7 physical rows written (7 SUCCESS_ROW_WRITTEN, 13 DUPLICATE_DETECTED). This confirms that raw Google Sheets API/Range operations are susceptible to read-then-write race conditions.
     * LOCKED Concurrency Boundary: Wrapping the lookup -> conditional append path inside LockService.getScriptLock() with tryLock(10000) reduced row generation to 1 physical row across 20 concurrent requests (1 SUCCESS_ROW_WRITTEN, 13 DUPLICATE_DETECTED, 6 LOCK_REJECTED).
     * Contention Latency Floor & Rejection: High request concurrency induces severe contention. Under a 10-second lock attempt, 6 out of 20 requests timed out waiting for the script lock, returning LOCK_REJECTED. Average transaction latency ballooned up to several seconds per lock cycle.

## Candidate Decisions Justified Now

1. GAS as Candidate First Adapter: Supported for low-throughput, cost-effective survey collection.
2. Google Sheets as Candidate First Persistence: Supported for low-concurrency storage (<10,000 rows), provided writes are guarded by script locking.
3. Adapter-Specific text/plain JSON Payload: Supported to enable readable cross-origin responses without triggering complex CORS preflight mandates on GAS.
4. Application-Level Status Parsing: Supported; the client architecture must evaluate the internal JSON payload structure (status: "SUCCESS" | "DUPLICATE" | "REJECTED") rather than raw HTTP status.
5. Concurrency Boundary Definition: Supported; duplicate check -> conditional append must be executed inside an atomic, synchronized critical section.

## Decisions That Remain OPEN

1. Locking Strategy (tryLock vs. waitLock): Whether to reject immediately/timeout or block until execution times out (GAS 6-minute ceiling).
2. Client-Generated Idempotency Key: The current schema lacks a dedicated, immutable idempotency_key distinct from survey/session identifiers.
3. Retry Policy & Backoff: Unverified whether LOCK_REJECTED or network disconnects can be retried automatically without risking duplicate submission or compounding lock contention.
4. Conflict Semantics (Same-ID / Different-Content): Unresolved whether payload mutations on the same ID represent an update, an attack, or a duplicate rejection.
5. Allowed Origins & Access Control: GAS /exec endpoints exposed to Anyone cannot enforce HTTP Origin header validation natively at the platform network boundary; app-level origin checking remains open.
6. Data Retention, Deletion, and Privacy: No governance model defined for processing GDPR/CCPR deletion requests against Google Sheets records.

## Additional Evidence Actually Required

 Before proceeding to a production candidate, the following minimal additional spikes are required:

  1. Client Idempotency Key & Retry Matrix Spike: Test client behavior when retrying an uncertain response (e.g., simulated client timeout while backend write succeeds). Verify if an explicit idempotency_key safely yields DUPLICATE_DETECTED on second arrival without duplicate side-effects.
  2. Locking Strategy Under Sustained Load: Compare tryLock(timeout) with exponential client retry against waitLock() to measure overall tail latency and failure distribution under sustained 5–10 requests/sec.
  3. Application Origin Validation Spike: Verify if e.parameter or request headers received by GAS reliably expose request origin for authorization checks across different user browsers.

## Decision Matrix

   | Decision | Repository Evidence | Outside Evidence | Classification | Recommendation | Remaining Gap |
   | ------------------- | -------------------------------- | ----------------------------------- | --------------------------------- | --------------------------------- | -------------------- |
   | GAS First Adapter | High (Spike 1/2) | Standard GAS runtime | SUPPORTED BY OBSERVATION | Adopt as candidate adapter | Cold start/spin-up latencies |
   | Sheets Persistence | High (Spike 2) | 10M cell limit | SUPPORTED BY OBSERVATION | Adopt for <10k scale | Performance degradation >10k rows |
   | text/plain JSON | High (Spike 1) | CORS spec | SUPPORTED BY OBSERVATION | Adopt for GAS adapter | Requires app-level JSON validation |
   | Readable Outcome Body | High (Spike 1) | GAS redirect behavior | SUPPORTED BY OBSERVATION | Adopt client body parser | Standardized outcome mapping |
   | ScriptLock Usage | High (Spike 2) | LockService API | SUPPORTED BY OBSERVATION | Mandate critical section | Granularity (Script vs Doc lock) |
   | tryLock Selection | Moderate (Spike 2) | GAS timeout limits | REASONABLE DESIGN INFERENCE | Open parameter | Optimal timeout value (e.g. 5s vs 10s) |
   | 10s Timeout Ceiling | Single test parameter | GAS 30s lock cap | REQUIRES ADDITIONAL SPIKE | Do not treat as production policy | Benchmark 2s, 5s, 10s under load |
   | Automatic Retry | None | Distributed systems | PREMATURE / UNSUPPORTED | DO NOT adopt yet | Risk of compounding lock queues |
   | Exponential Backoff | None | Standard retry patterns | REASONABLE DESIGN INFERENCE | Hold as candidate design | Needs validation against LOCK_REJECTED |
   | Idempotency Key | Partial (Survey ID) | Idempotency patterns | REQUIRES ARCHITECTURAL DECISION | Add explicit client key to schema | Data contract update required |
   | Same-ID / Same-Content | High (Spike 2) | N/A | SUPPORTED BY OBSERVATION | Treat as benign duplicate | Contract formalization |
   | Same-ID / Diff-Content | None | N/A | REQUIRES ARCHITECTURAL DECISION | Reject as illegal state/conflict | Governance policy definition |
   | Retention Policy | None | Legal compliance | REQUIRES ARCHITECTURAL DECISION | Open policy decision | Auto-archive / deletion workflow |
   | Deletion / Withdrawal | None | GDPR regulations | REQUIRES ARCHITECTURAL DECISION | Open policy decision | Deletion implementation in Sheets |
   | Allowed Origins | None | Web security | REQUIRES ADDITIONAL SPIKE | Validate at app layer | Origin spoofing limits in GAS |
   | Logging / Privacy | None | Google Cloud logging | REQUIRES ARCHITECTURAL DECISION | Strip PII from execution logs | PII exposure in stack traces |
   | Migration Threshold | None | Sheet performance | PREMATURE / UNSUPPORTED | Defer threshold selection | Performance benchmark at 5k+ rows |

## Minimum Production-Candidate Vertical Slice

 The smallest viable, architecturally sound vertical slice justified by current evidence consists of:

  1. Data Contract: Extend SurveyResponse schema to include a dedicated, client-generated idempotency_key (UUID v4).
  2. Client Transport: Cross-origin fetch issuing a POST with Content-Type: text/plain carrying JSON.
  3. GAS Backend:
    - Single doPost(e) entrypoint.
    - Guarded critical section using LockService.getScriptLock() and tryLock(5000).
    - Sequential lookup via TextFinder or in-memory array over idempotency_key.
    - Append to Google Sheet if absent.
    - Express response explicitly as 200 OK with JSON payload containing canonical status (SUCCESS_ROW_WRITTEN, DUPLICATE_DETECTED, or LOCK_REJECTED).
  4. Client Outcome Handling: Parse JSON response body. On LOCK_REJECTED or network drops, report a transient error to the user without blind background retries until retry semantics are validated.

## Claim-by-Claim Review of External Recommendation

 > Recommendation Statement:
 > "Results of the two spikes confirm readiness to implement the GAS adapter with mandatory LockService and text/plain CORS transport. To stabilize load behavior, the client should implement exponential backoff with jitter for LOCK_REJECTED. Long-term idempotency-key storage, Allowed Origins security, and UI handling of long lock waits remain open."
 >1.Claim 1: "Results of the two spikes confirm readiness to implement the GAS adapter with mandatory LockService and text/plain CORS transport."

   > - Evaluation: PARTIALLY SUPPORTED.

   > - Reasoning: Spike 1 and 2 prove technical feasibility of text/plain CORS transport and LockService protection (70eceb6, 391d52b). However, "readiness to implement" implies production readiness. Critical gaps in security (Allowed Origins) and data contract (idempotency key) prevent this from being a complete production specification.

 >2.Claim 2: "To stabilize load behavior, the client should implement exponential backoff with jitter for LOCK_REJECTED."

  > - Evaluation: PREMATURE.
  > - Reasoning: Neither spike tested client-side retries or backoff patterns. Under high lock contention, adding automatic retries (even with jitter) can aggravate lock queues, increase tail latency, and trigger secondary execution timeouts in GAS. Retries are unsafe without a proven, idempotent key lookup mechanism.
 >3.Claim 3: "Long-term idempotency-key storage, Allowed Origins security, and UI handling of long lock waits remain open."

 > - Evaluation: SUPPORTED.
 > - Reasoning: Correctly identifies that identity contracts, origin security, and user-facing latency management have not been resolved by the existing spike evidence (2026-08-22-live-browser-evidence.md, 2026-08-22-concurrency-persistence-evidence.md).

## Recommended Next Architecture Gate

### Gate Objective:

 Formally transition from experimental spikes to an Architecture Decision Record (ADR) update.

1. Step 1 (Data Contract Update): Submit an update to research/user-surveys/survey/spec/data-contract.md introducing an explicit idempotency_key field to the canonical SurveyResponse schema.
2. Step 2 (Targeted Retry Spike): Conduct a micro-spike testing client-side retries using the new idempotency_key against simulated network drops and LOCK_REJECTED outcomes to verify zero duplicate row generation.
3. Step 3 (ADR-0014 Resolution): Update ADR-0014 to promote GAS + Google Sheets to CANDIDATE_ADAPTER_1, specifying text/plain transport, LockService synchronization, explicit client idempotency keys, and explicit failure surfacing in UI.
