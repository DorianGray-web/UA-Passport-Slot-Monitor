**READ-ONLY Architecture & Evidence Review Complete**

I inspected the repository per the query using only allowed tools (list_dir, read_file, git_status, git_log). No files were edited, created, staged, or committed.

**Key artifacts reviewed:**

- `docs/DECISIONS.md` (ADR-0014 not yet recorded as Accepted; remains at proposal stage via spec)
- `research/user-surveys/survey/spec/transport-persistence.md` (defines the 5 canonical outcomes and lists 15+ OPEN items)
- `research/user-surveys/survey/spec/data-contract.md` (`response_id` is client-generated UUID v4 and the idempotency key)
- Spike material: `README.md`, `2026-08-22-live-browser-evidence.md`, `2026-08-22-concurrency-persistence-evidence.md`, `Code.gs`, harness
- `CHANGELOG.md` entries for commits `70eceb6` (transport spike) and `391d52b` (concurrency spike)
- Git history and current working tree

**Core findings (strictly distinguished):**

- Transport spike: In one tested Chrome + GitHub Pages + temporary Apps Script config, `text/plain` JSON POST with `cors` + redirect produced a readable 200 response from `script.googleusercontent.com`. The probe reached `doPost(e)` and parsed the body. HTTP 200 was returned for both valid and invalid probes. `no-cors` was opaque.
- Concurrency spike: Locked shared-ID path produced 1 physical row (13 DUPLICATE_DETECTED + 6 LOCK_REJECTED). Unlocked path produced 7 rows. Lock contention increased latency; `tryLock(10000)` rejections observed near timeout.
- Both spikes used non-canonical probes only. No `SurveyResponse v2` validation, no canonical outcomes, no production deployment/privacy controls, and no retention/deletion testing occurred.
- Many decisions listed as OPEN in `transport-persistence.md` remain OPEN. The spikes provide bounded feasibility evidence for one configuration and one read/check/append design, not universal platform guarantees or production readiness.

**Executive assessment**
Implementation of a production-candidate GAS/Sheets adapter is **not yet justified**. The spikes reduce some transport and basic concurrency risk but leave the majority of ADR-0014 OPEN items unresolved. A minimal technical prototype could be explored under strict isolation, but public exposure or vertical slice work is blocked.

**Evidence now established (repository + spikes only)**

- Readable CORS response after ContentService redirect is feasible in the tested browser path using `text/plain`.
- ScriptLock serialized the tested duplicate-check + append and preserved the single-row invariant for that design.
- HTTP 200 does not equal application success (observed with both `RECEIVED` and `INVALID_PROBE`).
- Lock contention materially affects latency and can produce acquisition failures near the configured timeout.
- `response_id` client-generated idempotency model and the five canonical outcomes are unchanged.

**Candidate decisions now justified**

- Browser transport feasibility for one configuration (text/plain + cors + readable response after redirect).
- ScriptLock as a possible concurrency boundary for a read/check/append Sheets design (implementation-specific, not universal).

**Decisions that must remain OPEN**
All others, including: first adapter selection, response semantics mapping, retry policy, idempotency lifetime, same-ID/different-content rules, retention/deletion, logging, deployment/allowed origins, locking scope and timeout policy, migration signals, and full privacy/security controls.

**Additional evidence required**

- Adapter profile that actually accepts/validates `SurveyResponse v2` and emits the five canonical outcomes.
- Browser-visible behavior under the chosen deployment access settings (allowed origins, actual status codes, preflight).
- Controlled tests of same-ID/same-content vs. same-ID/different-content.
- Privacy, logging, and lifecycle controls before any production exposure.

**Decision matrix** (selected rows)

| Decision | Current evidence | Classification | Recommendation | Remaining evidence |
| -------------------------------- | ----------------------------------- | --------------------------------- | --------------------------------- | -------------------- |
| GAS as first adapter | Bounded transport + concurrency spikes | REASONABLE DESIGN INFERENCE | Not yet; still blocked | Full adapter profile + privacy review |
| Sheets as first storage | Disposable experiment only | REASONABLE DESIGN INFERENCE | Not yet | Production mapping + lifecycle |
| text/plain JSON | Worked in tested path | SUPPORTED BY OBSERVATION | Adapter-specific only | Broader browser + deployment testing |
| Readable CORS response | Observed in one config | SUPPORTED BY OBSERVATION | Feasible for prototype | Production deployment model |
| Application-level outcome body | HTTP 200 + body observed | SUPPORTED BY OBSERVATION | Required; mapping unresolved | Canonical outcome emission tests |
| ScriptLock critical section | Protected single-row invariant | SUPPORTED BY OBSERVATION | Justified for this design | Alternative designs |
| tryLock | Used; rejections observed | SUPPORTED BY OBSERVATION | Experimental parameter only | Policy decision |
| Lock timeout (10s) | Experimental value | PREMATURE / UNSUPPORTED | Not production-backed | UX + operational analysis |
| Automatic retry | LOCK_REJECTED observed | PREMATURE / UNSUPPORTED | Do not select yet | Idempotency + failure class analysis |
| Exponential backoff + jitter | Not tested | PREMATURE / UNSUPPORTED | Do not select | Safe retry model |
| Client idempotency identity | `response_id` per contract | SUPPORTED BY OFFICIAL DOC | Preserve; no new ID | Same-ID/different-content rule |
| Retention / deletion | Not tested | PREMATURE / UNSUPPORTED | Blocks production | Privacy + lifecycle decisions |
| Allowed origins / logging | Not tested | PREMATURE / UNSUPPORTED | Blocks production | Security/privacy review |
| Migration threshold | None in spikes or repo | PREMATURE / UNSUPPORTED | Use qualitative signals only | Scale evidence |

**Minimum production-candidate vertical slice**
Technically implementable now (isolated): A throwaway adapter that accepts a frozen `SurveyResponse v2` payload, performs basic validation, emits one of the five canonical outcomes, and uses the locked read/check/append pattern under a test deployment with no real data.

Safe to expose publicly now: None. Privacy, deployment visibility, logging, retention, deletion, and full contract integration gates are not cleared.

**Review of the external Google AI recommendation**
"Results of the two spikes confirm readiness to implement the GAS adapter with mandatory LockService and text/plain CORS transport. To stabilize load behavior, the client should implement exponential backoff with jitter for LOCK_REJECTED."

- "confirm readiness to implement the GAS adapter" → **premature** (spikes used probes only; no canonical contract, validation, or outcomes).
- "with mandatory LockService" → **partially supported** (required for the tested design; not proven mandatory for all designs).
- "text/plain CORS transport" → **partially supported** (worked in tested path; adapter-specific, not yet contract-level).
- "client should implement exponential backoff with jitter for LOCK_REJECTED" → **premature / unsupported** (no retry policy selected in ADR-0014; different failure classes not distinguished; idempotency safety not established).

**Suggested next architecture action**
Hold an explicit ADR review to decide whether to record ADR-0014 (with current OPEN items) and scope a narrowly bounded next spike that implements canonical outcome emission + validation before any persistence or retry work.
