# Independent Architecture/Evidence Review — Apps Script Survey Spikes vs. ADR-0014

**Repository:** DorianGray-web/UA-Passport-Slot-Monitor
**Branch:** `spike/survey-pages-transport`
**Reviewed commits:** `70eceb6` (transport spike), `391d52b` (concurrency spike)
**Review type:** read-only, no code/ADR changes proposed

---

## Executive assessment

Three separate claims must not be collapsed into one:

| Claim | Status |
| --- | --- |
| **Technically implementable** — a browser can reach Apps Script and get a readable ack; a ScriptLock-protected Sheet path can prevent a duplicate row in one tested burst | **Yes**, for the exact tested configuration |
| **Justified production candidate** — GAS + Sheets is architecturally reasonable as the *first* adapter to build against ADR-0014's adapter-neutral contract | **Yes, conditionally** — but only as a candidate to prototype behind the contract, not as an approved production choice |
| **Safe for public deployment** | **No.** Security (Allowed Origins, abuse prevention, deployment visibility), privacy/retention, timeout/retry policy, and idempotency lifetime are all still OPEN in the repository's own spec |

Both spikes are internally consistent, honestly self-limiting, and match their own evidence-classification tables against what's actually committed — this was checked, not assumed. Neither spike, individually or combined, resolves a single OPEN item in `transport-persistence.md §17` to an *approved* decision; they narrow several from "unknown" to "candidate with bounded evidence." The distinction the prompt asks me to enforce — bounded-experiment success ≠ production policy — is one the repository's own evidence documents already enforce rigorously (their NOT PROVEN / NOT SUPPORTED rows). My review mostly checks whether that self-discipline holds up, and where it should go further.

One thing the documents don't flag but should: the **concurrency-spike Apps Script/Sheets code itself was never committed** ("disposable," "not retained" per the README and evidence report). Only the transport probe's `Code.gs` is in the repo, and it does no Sheets/Lock work at all (verified — no `LockService`, `SpreadsheetApp`, `CacheService`, or logging calls). So the concurrency numbers are **narrative evidence supplied by the project owner and transcribed into a document**, not evidence independently reproducible from repository artifacts. That doesn't make the numbers false, but it changes their evidence class: they're closer to "trusted first-party report" than "verifiable-from-repo observation," and that gap should itself be logged as a gap.

---

## Evidence established by Spike 1 (transport, `70eceb6`)

Verified against `2026-08-22-live-browser-evidence.md`, `Code.gs`, `harness/probe.js`, `README.md`.

- A GitHub Pages-origin browser using `fetch(..., {mode:'cors'})` reached a temporary Apps Script `/exec` deployment for both GET and a `text/plain` POST carrying a JSON body, and read a `ContentService` JSON acknowledgement after the `302` redirect to `script.googleusercontent.com` — no proxy involved. This is real application-level evidence, not just transport-level: the response could only be constructed *after* `doPost(e)` parsed `e.postData.contents`, so it proves the round trip through parsing, not just dispatch.
- `no-cors` POST produced only an opaque `status:0` response — correctly logged as dispatch-only evidence, not receipt evidence.
- HTTP 200 was returned for both `RECEIVED` and `INVALID_PROBE` bodies — correctly used to establish that **HTTP status alone cannot carry the application outcome**; the outcome has to live in the body.
- The retained `Code.gs` matches the document's safety claims: no Sheets/Lock/Cache/log calls, doesn't echo the POST body, caps body length at 4096 chars.

This is real, checkable, narrow feasibility evidence for one browser/Chrome/one deployment config on one day. It says nothing about other browsers, other deployment access modes, or the production contract.

## Evidence established by Spike 2 (concurrency, `391d52b`)

Verified against `2026-08-22-concurrency-persistence-evidence.md` and `CHANGELOG.md`.

- LOCKED shared-ID burst (20 requests, same `probe_id`, `tryLock(10000)`): 1 `SUCCESS_ROW_WRITTEN`, 13 `DUPLICATE_DETECTED`, 6 `LOCK_REJECTED`, 1 physical row afterward. Confirmed against the table in the doc — numbers match exactly, including per-request lock-wait times.
- UNLOCKED shared-ID negative control (same burst shape, lock bypassed): 7 `SUCCESS_ROW_WRITTEN`, 13 `DUPLICATE_DETECTED`, 7 physical rows. Confirmed.
- This is a legitimate controlled comparison (one variable changed — presence of the lock), and it does demonstrate a duplicate-write race exists without the lock and is prevented by it, in this one run.
- Lock contention was substantial: successful requests took up to ~11.8 s of client-visible latency in the unique-ID burst; several `LOCK_REJECTED` results clustered right at the 10 s configured timeout, which the document correctly reads as "timeout boundary observed," not "10 s is the right production number."
- **As noted above, the actual Sheets/Lock implementation code that produced these numbers is not in the repository.** The evidence document is the only artifact; there's no harness script to independently audit for e.g. whether the duplicate check used a cached read, a fresh `TextFinder` call, or something else. That's a gap in *auditability*, separate from whether the reported numbers are accurate.

---

## Candidate decisions justified now

These can reasonably move from "unknown" to "candidate for the first implementation attempt," pending the gates already listed in the repo's own `transport-persistence.md §17/§19`:

- **GAS as first adapter to prototype** — reasonable candidate; not yet a production choice.
- **Google Sheets as first storage to prototype** — reasonable candidate; same caveat.
- **`text/plain` + JSON body as the POST encoding** — justified as *a* working encoding under CORS; not shown to be the *only* one, and not yet approved as the adapter profile.
- **A readable ContentService body (not just HTTP status) as the outcome channel** — justified; HTTP-status-only was affirmatively falsified by the spike itself.
- **`LockService.getScriptLock()` wrapping "duplicate lookup → conditional append" as a single critical section** — justified as the mechanism that prevented the observed race, for this specific hazard.

## Decisions that remain OPEN (must not be inferred from these spikes)

Everything else in `transport-persistence.md §17`, and specifically:

- `tryLock()` vs `waitLock()` — the spike used `tryLock`, so it demonstrates *tryLock's* rejection behavior; it says nothing comparative about `waitLock`, which has different UX/latency tradeoffs (blocks instead of failing fast).
- 10 s as a production timeout — that was the *tested parameter*, not a derived value. The doc itself flags this correctly.
- Automatic retry of any kind, and exponential backoff/jitter specifically — see the dedicated section below; this is the weakest part of the external recommendation.
- Idempotency lifetime, same-ID/same-content and same-ID/different-content semantics — untouched by either spike. Notably, `data-contract.md`'s own implementation gates flag that `response_id` is currently **regenerated with a new `submitted_at` on repeated submits** in the client — which actively works against the "frozen payload" retry invariant `transport-persistence.md §8` assumes. This is a live contract-level gap, not a hypothetical.
- Retention, deletion/withdrawal, backup lifecycle — untouched.
- Allowed Origins, deployment visibility, abuse prevention, access controls, secrets — untouched. The transport spike used a *temporary* deployment with unrecorded access settings; that's explicitly logged as NOT PROVEN in its own evidence table.
- Logging / processor / data region — untouched.
- Sheets internals (TextFinder vs. in-memory lookup, row mapping, formula protection, append strategy) — untouched; the concurrency spike's actual lookup mechanism isn't even auditable from the repo.
- Any fixed migration threshold (20k/30k/50k rows) — no evidence anywhere in either spike; this number doesn't appear in the repository at all.

---

## Additional evidence actually required

Kept minimal — not proposing interesting-but-unnecessary experiments:

1. **A retained, committed concurrency-spike implementation** (or at least the actual duplicate-check/append code as it existed during the run) so the Phase 1–3 results are auditable rather than narrated. This is a documentation/evidence-integrity gap, not a new experiment.
2. **One experiment comparing `tryLock()` failure behavior against `waitLock()` blocking behavior** under the same burst shape, if `waitLock` is a live candidate — needed before choosing between fail-fast-with-client-retry and block-and-wait as the production posture.
3. **A single experiment on retry-after-`TEMPORARY_FAILURE`/timeout using a frozen (non-regenerated) `response_id` + `submitted_at`**, once the client-side "gates" fix stops regenerating `submitted_at` on resubmission — this is a precondition for any idempotency-lifetime experiment, not something to test yet.
4. **A deployment-visibility/Allowed-Origins probe** under the actual candidate access mode (not a temporary personal deployment) before any security sign-off — this is a different risk surface than what was tested.

Nothing else (migration thresholds, backup lifecycle, formal load testing) is justified yet; those are premature relative to a "smallest vertical slice."

---

## Decision matrix

| Decision | Repository evidence | Outside evidence if used | Classification | Recommendation | Remaining gap |
| --- | --- | --- | --- | --- | --- |
| GAS first adapter | `70eceb6` transport spike | Google Apps Script Web Apps docs (dispatch to `doGet`/`doPost`) | REASONABLE DESIGN INFERENCE | Candidate for prototype behind adapter contract | Not an approved production choice; ADR-0014 still Proposed |
| Sheets first persistence | `391d52b` concurrency spike | — | REASONABLE DESIGN INFERENCE | Candidate for prototype | Sheets mapping/locking/formula-protection profile not written |
| `text/plain` + JSON body | Live browser evidence, valid POST | — | SUPPORTED BY OBSERVATION | Adopt for prototype | Not shown to be only/best encoding; media-type policy still OPEN |
| CORS-readable acknowledgement | Live browser evidence, GET+POST | Apps Script ContentService redirect docs | SUPPORTED BY OBSERVATION + DOCUMENTATION | Adopt as outcome channel | One browser, one deployment config, unrecorded access mode |
| Application-level outcome body (not HTTP status) | `INVALID_PROBE` vs `RECEIVED` both HTTP 200 | — | SUPPORTED BY OBSERVATION | Adopt | Concrete response schema/status mapping still OPEN |
| ScriptLock around lookup→append | Phase 2 vs Phase 3 comparison | — | SUPPORTED BY OBSERVATION (bounded) | Adopt for the specific race it addresses | Not shown for other hazards (e.g., cross-lock storage failures) |
| `tryLock()` | Used throughout concurrency spike | — | SUPPORTED BY OBSERVATION (of tryLock specifically) | Provisional default | Not compared against `waitLock()`; REQUIRES ADDITIONAL SPIKE if `waitLock` is a real candidate |
| 10 s lock timeout | Configured experimental parameter | — | PREMATURE as production value | Do not fix yet | Only the tested value; no sensitivity analysis |
| Automatic retry | Not tested | — | UNSUPPORTED / REQUIRES ARCHITECTURAL DECISION | Reject as-is | See retry section below |
| Exponential backoff + jitter | Not tested | General distributed-systems practice (outside evidence) | PREMATURE | Do not adopt yet | No retry-eligibility classification exists yet (see below) |
| Idempotency identity (`response_id`) | `data-contract.md` defines it; not tested for retry | — | REQUIRES ARCHITECTURAL DECISION | Fix client `submitted_at` regeneration bug first | Contract gap actively undermines "frozen payload" retry model |
| Same-ID/same-content | Not addressed | — | REQUIRES ARCHITECTURAL DECISION | Open | No spike touched equality/comparison rules |
| Same-ID/different-content | Not addressed | — | REQUIRES ARCHITECTURAL DECISION | Open | Explicitly flagged OPEN in `transport-persistence.md §14` |
| Retention | Not addressed | — | REQUIRES ARCHITECTURAL DECISION | Open, blocks `PRIVACY.md` update | No lifecycle decision anywhere |
| Deletion/withdrawal | Not addressed | — | REQUIRES ARCHITECTURAL DECISION | Open | Interacts with idempotency-evidence deletion, also OPEN |
| Allowed Origins | Not tested (temporary deployment, unrecorded access mode) | — | PREMATURE / UNSUPPORTED | Requires dedicated security-profile spike | Deployment access/execute-as settings explicitly NOT PROVEN |
| Logging/privacy | Not addressed by either spike | — | REQUIRES ARCHITECTURAL DECISION | Open | `transport-persistence.md §10` lists 9 open sub-items, none touched |
| Migration threshold (20k/30k/50k) | No reference anywhere in repo | — | UNSUPPORTED | Do not adopt any figure | No row-count or performance-scaling evidence exists |

---

## Minimum production-candidate vertical slice

Given the evidence actually in hand, the smallest defensible next step is a **single-outcome, single-adapter prototype**, not a production deployment:

1. Implement a GAS adapter that accepts exactly one `survey_response/2.0.0` object (per ADR-0014 §Decision), performs the `§7` validation boundary server-side, and maps to exactly the five canonical outcomes — not the probe's `RECEIVED`/`INVALID_PROBE` labels.
2. Wrap duplicate-check + append in `LockService.getScriptLock()` with `tryLock()`, using a timeout chosen and documented as a starting parameter, explicitly flagged as unvalidated for production load.
3. Fix the client `response_id`/`submitted_at` regeneration-on-resubmit bug (already listed as a known gate item) before any idempotency behavior is layered on top — otherwise "frozen payload" retry has no floor to stand on.
4. No automatic retry, no backoff, on this slice. Surface `TEMPORARY_FAILURE`/timeout to the user as "unknown outcome," consistent with `transport-persistence.md §9`.
5. Deploy to a *reviewed* (not throwaway) test deployment with recorded, deliberate execute-as/access settings, specifically to close the "deployment access NOT PROVEN" gap — this is a prerequisite for any Allowed-Origins decision, not an optional nicety.
6. No retention/deletion policy implemented yet; store nothing this slice can't immediately be asked to be deleted, and keep the sheet disposable/test-only until `PRIVACY.md` is updated.

This slice deliberately does not attempt idempotency lifetime, retry, security hardening, or scale — those remain OPEN and require separate approval, matching the repo's own gating structure.

---

## Claim-by-claim review of the external recommendation

> "Results of the two spikes confirm readiness to implement the GAS adapter with mandatory LockService and text/plain CORS transport. To stabilize load behavior, the client should implement exponential backoff with jitter for LOCK_REJECTED. Long-term idempotency-key storage, Allowed Origins security, and UI handling of long lock waits remain open."

| Claim | Status | Reasoning / evidence location |
| --- | --- | --- |
| "Confirm readiness to implement the GAS adapter" | **PARTIALLY SUPPORTED** | Spikes support GAS as a *candidate* worth prototyping (§ above); "readiness" overstates it — ADR-0014 is still `Proposed`, and `transport-persistence.md §19` explicitly lists implementation gates not yet met (client payload gaps, idempotency/timeout/origin approval, contract tests). "Confirmed" is the wrong word for "candidate, pending gates." |
| "mandatory LockService" | **SUPPORTED** for the specific lookup→append hazard | Phase 2 vs Phase 3 comparison is a real controlled result. "Mandatory" is fine as a design conclusion for *this* race, but shouldn't be generalized to "mandatory for all Sheets writes" — the spike only tested this one critical section. |
| "text/plain CORS transport" | **SUPPORTED** as a working, tested encoding | Live browser evidence, valid POST section. Not shown to be the *only* viable encoding — HTTP method/media-type policy is still listed OPEN in `transport-persistence.md §5`. |
| "exponential backoff with jitter for LOCK_REJECTED" | **UNSUPPORTED** | Neither spike tested any retry. `LOCK_REJECTED` in the spike meant "this probe didn't acquire its lock within 10 s" — it says nothing about whether a retry would succeed, contend further, or hit the same wall, and nothing about client-side retry storms making contention worse. This is the recommendation's weakest link: an observed rejection state is being used to justify an entire retry *policy* that was never exercised. Per `transport-persistence.md §9`, automatic retry, retry classes, and backoff are explicitly unselected. Should be REQUIRES ADDITIONAL SPIKE at minimum, more honestly REQUIRES ARCHITECTURAL DECISION (retry policy also needs a decision on *which* failure classes are retry-eligible — see below). |
| "Long-term idempotency-key storage... remain open" | **SUPPORTED** (as an open item) | Matches `transport-persistence.md §8/§17` and `data-contract.md`'s known `response_id`/`submitted_at` regeneration gap. Correctly left open. |
| "Allowed Origins security... remain open" | **SUPPORTED** (as an open item) | Matches `transport-persistence.md §11` and the transport spike's own "deployment access NOT PROVEN" row. Correctly left open. |
| "UI handling of long lock waits... remain open" | **SUPPORTED** (as an open item) | No UI/timeout-UX decision exists anywhere in the repo; consistent with `§9`'s "manual retry UX" being unselected. |

**On retry reasoning specifically** (question 12): the five failure modes named in the review prompt need different treatment, and the repo's spec already gestures at this distinction without fully spelling it out:

- **Definite pre-write rejection** (e.g., `LOCK_REJECTED` before any write attempted, or `INVALID_REQUEST`) — retry-eligible in principle for transient ones (`LOCK_REJECTED`), never for `INVALID_REQUEST` (won't change on retry without a different payload).
- **Network failure before receipt** — safe to retry with the same frozen payload once idempotency identity is trustworthy, because nothing was accepted.
- **Successful commit, lost acknowledgement** — this is exactly why `DUPLICATE_ACCEPTED` exists as a distinct outcome; a naive retry-without-idempotency-check would double-write. Retry is safe *only if* the backend's duplicate detection is trustworthy — which is the one thing the concurrency spike actually tested and supports, narrowly.
- **Client timeout while execution may continue** — the spike calls this "no observed outcome... do not claim success or failure" (`transport-persistence.md §9`); retry logic here has to tolerate a possible eventual duplicate, which again depends on the untested idempotency-lifetime/equality rules.
- **Duplicate retry after an uncertain result** — this is the case the concurrency spike speaks to most directly, but only for a single lookup+append inside one lock scope, not across a network-level client retry with a fresh HTTP request.

None of this adds up to "implement exponential backoff now" — it adds up to "the failure taxonomy needs to exist as an approved decision before any retry code is written," which is what the repo's own OPEN list already says.

---

## Recommended next architecture gate

Before writing adapter code beyond a disposable prototype:

1. Approve or reject GAS+Sheets as the *reviewed* first-adapter profile (not just "candidate") — this is an ADR-0014 decision, not something this review makes.
2. Land the client-side `response_id`/`submitted_at` fix (already a known gate item) so idempotency has a stable identity to reason about.
3. Decide the failure-class → retry-eligibility mapping *before* any backoff/jitter implementation — treat this as its own small architectural decision, not a corollary of the concurrency spike.
4. Run the reviewed-deployment Allowed-Origins/access-mode check as a dedicated, non-disposable experiment, since the current evidence explicitly says deployment access settings were not captured.
5. Only after 1–4: greenlight the minimum vertical slice described above, still without production retention/deletion/retry until those are separately approved.

No code changes, ADR edits, or PRs were made as part of this review, per the stated constraints.
