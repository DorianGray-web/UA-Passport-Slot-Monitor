# Apps Script concurrency and disposable persistence evidence

- **Date:** 2026-08-22
- **Status:** Completed bounded research experiment
- **Scope:** Temporary Apps Script Web App and disposable Google Sheet
- **Production status:** Not approved and not implemented

## Evidence classes

- **DOCUMENTED** — experiment configuration or behavior recorded by the
  experiment implementation.
- **OBSERVED** — browser response/timing output or post-run Sheet state recorded
  during the experiment.
- **INFERRED** — the narrow interpretation supported by those observations.
- **NOT PROVEN** — a plausible conclusion that the experiment did not establish.
- **NOT SUPPORTED** — a conclusion contradicted by the experiment boundary or
  requiring evidence outside it.

The values below are sanitized records from the completed experiment. This
report does not claim a fresh reproduction. No deployment URL, redirect
capability URL, spreadsheet ID, account identifier, or personal data is
retained.

## Research questions

The experiment investigated whether, in one disposable implementation:

1. `LockService.getScriptLock()` serialized a concurrent duplicate-check and
   append critical section;
2. `lock.tryLock(timeout_ms)` returned failures under sustained contention;
3. duplicate lookup and append preserved a single-row invariant while both
   operations were protected by the script lock;
4. lock contention affected client-visible latency; and
5. bypassing the lock reproduced a duplicate-write race.

It did not evaluate the canonical `SurveyResponse v2` contract, production
storage design, retention, deletion, retry, or ADR-0014 outcome mapping.

## Experimental path

**DOCUMENTED:** The disposable handler parsed a JSON-encoded `text/plain`
request body and selected either `LOCKED` or `UNLOCKED` mode. The locked path
obtained `LockService.getScriptLock()`, called `tryLock(timeout_ms)`, and, only
after acquisition, read the disposable Sheet, searched for `probe_id`, and
either appended one row or reported an existing duplicate. It released the
lock in `finally`. The unlocked negative control retained the duplicate lookup
and append but bypassed the lock.

The probe emitted these experimental status labels:

- `SUCCESS_ROW_WRITTEN`
- `DUPLICATE_DETECTED`
- `LOCK_REJECTED`
- `UNLOCKED_EXECUTION`
- `EXECUTION_FAILED`

These labels describe the probe only. They do not add to, replace, or map the
ADR-0014 canonical outcomes.

## Phase 0 — single locked baseline

### Browser observation

**OBSERVED:** One locked request sent after the burst completed in 1814.5 ms.
The browser recorded HTTP 200, `response.type = "cors"`, and
`redirected = true`. The readable response contained:

```text
status: SUCCESS_ROW_WRITTEN
server_received_at: 1787411803608
lock_wait_ms: 67
lock_acquired_at: 1787411803677
write_completed_at: 1787411804277
```

### Interpretation

**OBSERVED:** This one request had 67 ms of reported lock wait and about
1.8 seconds of client-visible latency.

**NOT PROVEN:** It does not establish a universal Apps Script baseline, an
approximately 1.8-second latency floor, or a lower bound on request latency.

## Phase 1 — locked unique-ID burst

### Configuration

**DOCUMENTED:** 20 requests, 50 ms stagger, `LOCKED` mode, 10000 ms lock
timeout, and a unique `probe_id` per request.

### Browser observations

| Index | Client latency (ms) | Status |
| ---: | ---: | --- |
| 1 | 2170 | `SUCCESS_ROW_WRITTEN` |
| 4 | 3292 | `SUCCESS_ROW_WRITTEN` |
| 0 | 4133 | `SUCCESS_ROW_WRITTEN` |
| 8 | 4341 | `SUCCESS_ROW_WRITTEN` |
| 2 | 5693 | `SUCCESS_ROW_WRITTEN` |
| 3 | 6821 | `SUCCESS_ROW_WRITTEN` |
| 9 | 7206 | `SUCCESS_ROW_WRITTEN` |
| 7 | 8862 | `SUCCESS_ROW_WRITTEN` |
| 13 | 9838 | `SUCCESS_ROW_WRITTEN` |
| 15 | 10970 | `LOCK_REJECTED` |
| 5 | 11485 | `LOCK_REJECTED` |
| 10 | 11259 | `LOCK_REJECTED` |
| 17 | 10912 | `LOCK_REJECTED` |
| 6 | 11572 | `LOCK_REJECTED` |
| 19 | 10960 | `LOCK_REJECTED` |
| 16 | 11124 | `LOCK_REJECTED` |
| 18 | 11067 | `LOCK_REJECTED` |
| 12 | 11564 | `SUCCESS_ROW_WRITTEN` |
| 14 | 11586 | `SUCCESS_ROW_WRITTEN` |
| 11 | 11771 | `LOCK_REJECTED` |

**OBSERVED:** The supplied results contain 11 `SUCCESS_ROW_WRITTEN` and 9
`LOCK_REJECTED` responses. Total client duration was 12335.931884765625 ms.
Requests completed out of index order, successful requests had substantially
different durations, and some succeeded after prolonged contention. Lock
rejections appeared around the configured 10-second acquisition timeout.

### Interpretation

**INFERRED:** In this burst, the script lock serialized entry to the protected
critical section, and contention for that section was a major contributor to
client-visible latency.

**NOT PROVEN:** The run did not establish FIFO ordering, lock fairness, a
universal concurrency limit, a universal rejection density, a latency curve,
or production throughput. `LOCK_REJECTED` means only that this probe did not
acquire its experimental script lock within the configured timeout; it is not
evidence of HTTP or server overload.

## Phase 2 — locked shared-ID atomicity experiment

### Configuration

**DOCUMENTED:** 20 concurrent requests used the same `probe_id`, `LOCKED`
mode, and an approximately 10000 ms lock timeout.

### Browser observations

| Index | Client latency (ms) | Status | Lock wait (ms) |
| ---: | ---: | --- | ---: |
| 0 | 3703 | `DUPLICATE_DETECTED` | 916 |
| 1 | 9320 | `DUPLICATE_DETECTED` | 6650 |
| 2 | 12399 | `LOCK_REJECTED` | 10067 |
| 3 | 10855 | `DUPLICATE_DETECTED` | 8729 |
| 4 | 7141 | `DUPLICATE_DETECTED` | 3560 |
| 5 | 4197 | `DUPLICATE_DETECTED` | 1767 |
| 6 | 1984 | `SUCCESS_ROW_WRITTEN` | 109 |
| 7 | 8053 | `DUPLICATE_DETECTED` | 6118 |
| 8 | 7460 | `DUPLICATE_DETECTED` | 5605 |
| 9 | 11807 | `DUPLICATE_DETECTED` | 9215 |
| 10 | 4717 | `DUPLICATE_DETECTED` | 2742 |
| 11 | 11451 | `LOCK_REJECTED` | 10143 |
| 12 | 9826 | `DUPLICATE_DETECTED` | 8019 |
| 13 | 11286 | `DUPLICATE_DETECTED` | 9688 |
| 14 | 11100 | `LOCK_REJECTED` | 10057 |
| 15 | 9199 | `DUPLICATE_DETECTED` | 7239 |
| 16 | 11199 | `LOCK_REJECTED` | 10046 |
| 17 | 11259 | `LOCK_REJECTED` | 10061 |
| 18 | 11597 | `DUPLICATE_DETECTED` | 9954 |
| 19 | 10964 | `LOCK_REJECTED` | 10148 |

**OBSERVED:** Total duration was 12510 ms. Exactly one request returned
`SUCCESS_ROW_WRITTEN`, 13 lock-acquiring requests returned
`DUPLICATE_DETECTED`, and 6 returned `LOCK_REJECTED` after failing to acquire
the lock within approximately the configured timeout.

### Sheet observation

**OBSERVED:** Inspection of the disposable Sheet after this locked experiment
found exactly one physical row for the shared `probe_id`.

### Interpretation

**INFERRED:** For this tested execution path and contention level, keeping the
duplicate lookup and append inside the same ScriptLock-protected critical
section preserved the intended single-row invariant.

**NOT PROVEN:** This is not evidence of exactly-once delivery, database
transaction semantics, crash-safe idempotency, durable production guarantees,
or guarantees across deployment, code, or configuration changes.

## Phase 3 — unlocked shared-ID negative control

### Configuration

**DOCUMENTED:** 20 requests used the same shared `probe_id`, `UNLOCKED` mode,
and a 50 ms stagger. Duplicate lookup and append remained, but lock acquisition
was bypassed.

### Browser observations

| Index | Client latency (ms) | Status |
| ---: | ---: | --- |
| 0 | 2135 | `SUCCESS_ROW_WRITTEN` |
| 8 | 1792 | `SUCCESS_ROW_WRITTEN` |
| 6 | 2575 | `SUCCESS_ROW_WRITTEN` |
| 10 | 2526 | `SUCCESS_ROW_WRITTEN` |
| 1 | 2974 | `SUCCESS_ROW_WRITTEN` |
| 15 | 2391 | `DUPLICATE_DETECTED` |
| 13 | 2487 | `SUCCESS_ROW_WRITTEN` |
| 9 | 2739 | `DUPLICATE_DETECTED` |
| 5 | 3012 | `DUPLICATE_DETECTED` |
| 3 | 3128 | `DUPLICATE_DETECTED` |
| 14 | 2611 | `DUPLICATE_DETECTED` |
| 4 | 3146 | `SUCCESS_ROW_WRITTEN` |
| 19 | 2414 | `DUPLICATE_DETECTED` |
| 2 | 3258 | `DUPLICATE_DETECTED` |
| 12 | 2770 | `DUPLICATE_DETECTED` |
| 7 | 3075 | `DUPLICATE_DETECTED` |
| 11 | 2890 | `DUPLICATE_DETECTED` |
| 17 | 2614 | `DUPLICATE_DETECTED` |
| 18 | 2578 | `DUPLICATE_DETECTED` |
| 16 | 2736 | `DUPLICATE_DETECTED` |

**OBSERVED:** Total client duration was 3537.72705078125 ms. Seven requests
returned `SUCCESS_ROW_WRITTEN`, 13 returned `DUPLICATE_DETECTED`, and this
negative-control path had no lock waiting.

### Sheet observation

**OBSERVED:** Inspection of the disposable Sheet after the unlocked experiment
found seven physical rows with the shared `probe_id`.

### Interpretation

**INFERRED:** The unprotected read/check/append sequence was race-prone in this
tested concurrent scenario. Multiple executions could observe absence before
another execution's append became visible to their duplicate check.

**NOT PROVEN:** The observations do not reveal Google's internal execution,
container, or scheduling topology.

## Controlled comparison

| Path | Requests | Physical rows | `SUCCESS_ROW_WRITTEN` | `DUPLICATE_DETECTED` | `LOCK_REJECTED` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Locked shared ID | 20 | 1 | 1 | 13 | 6 |
| Unlocked shared ID | 20 | 7 | 7 | 13 | 0 |

**INFERRED:** For the tested Apps Script and disposable Google Sheet
implementation on 2026-08-22, protecting duplicate lookup and append with a
ScriptLock prevented the duplicate-write race observed in the corresponding
unlocked negative control. The lock was required by the tested design to
preserve its single-row invariant.

**NOT SUPPORTED:** The comparison does not establish that LockService is
universally mandatory for Google Sheets idempotency. It does not turn the
single-row mechanism into exactly-once delivery.

## Latency evidence

**OBSERVED:**

- the single post-burst baseline was about 1815 ms with 67 ms reported lock
  wait;
- unlocked negative-control requests ranged from about 1.8 to 3.3 seconds in
  this run;
- locked contention extended client-visible durations to about 12 seconds;
  and
- many failed lock acquisitions reported waits near the configured 10-second
  timeout.

**INFERRED:** Contention on this critical section can materially increase
response latency. Serialization created a throughput/latency trade-off, and
`tryLock(10000)` produced an observable application-level failure boundary
around its configured timeout in this run.

**NOT PROVEN:** The data does not establish an immutable 2–3 second Apps Script
latency floor, a 10-second infrastructure concurrency limit, production
p95/p99, or that this burst represents expected survey traffic.

## Earlier HTTP 403 observation

**OBSERVED:** An earlier attempt to issue a more simultaneous browser burst
received HTTP 403 responses from direct POST requests to the temporary
`/exec` deployment. With a 50 ms stagger, later runs reached the application
path and completed the previously documented
`script.google.com` 302 redirect to a readable `script.googleusercontent.com`
HTTP 200 response.

**NOT PROVEN:** The cause of the earlier HTTP 403 responses was not established.
They occurred before application-level lock evidence was available and must
not be interpreted as `LOCK_REJECTED` or as a LockService result.

## Claim boundary

### Supported within the tested configuration

- **OBSERVED:** Locked and unlocked browser outcomes and latencies listed in
  this report.
- **OBSERVED:** One physical shared-ID row after the locked experiment and
  seven after the unlocked negative control.
- **INFERRED:** ScriptLock serialized the tested critical section.
- **INFERRED:** The protected lookup-plus-append preserved the tested
  single-row invariant, while bypassing the lock exposed a duplicate-write
  race.
- **INFERRED:** Lock contention materially contributed to latency and caused
  application-level acquisition failures near the configured timeout.

### Not established

- **NOT PROVEN:** FIFO or fair lock scheduling, universal concurrency or
  throughput limits, latency percentiles, production durability, crash
  behavior, or behavior under different deployments and configurations.
- **NOT SUPPORTED:** Production persistence readiness, a finalized
  `SurveyResponse v2` storage adapter, production idempotency guarantees,
  exactly-once delivery, or arbitrary-concurrency support.
- **NOT SUPPORTED:** Any change to ADR-0014 canonical outcomes, retry, timeout,
  storage, retention, deletion, deployment, or adapter decisions.

## Repository boundary

The disposable Apps Script implementation and Sheet were experimental
infrastructure and are not retained here. The committed `Code.gs` remains the
non-persistent transport probe from the earlier experiment. This report is
research input for a later adapter feasibility decision; it does not authorize
production code or modify the canonical survey contract.
