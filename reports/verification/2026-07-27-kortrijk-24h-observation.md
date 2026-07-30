# Verification Report: Kortrijk 24-Hour Queue Observation

> **Historical architecture note:** This report accurately records the
> page-level implementation tested on 2026-07-26/27. Its Playwright fallback
> conclusion was later superseded for normal monitoring by frontend 7.34.2
> call-site evidence and [ADR-0007/ADR-0008](../../docs/DECISIONS.md).
> Current monitors are HTTP-only; browser automation is confined to separate
> diagnostics and research. The original observations below are preserved as
> historical evidence.

**Observation period:** 2026-07-26 23:55:15 — 2026-07-27 23:56:09

**Duration:** approximately 24 hours and 54 seconds

**Monitor:** `providers/dp-document/kortrijk_monitor.py`

**Verdict:** PASS_WITH_GAPS

`PASS_WITH_GAPS` means that continuous operation, fallback behaviour, backoff,
and automatic recovery were verified, while real slot availability and CAPTCHA
workflows were not observed.

## Purpose

Verify that the Kortrijk queue monitor can operate continuously, classify the
publicly visible queue state, use direct HTTP observation when possible, fall
back to a browser session when required, and recover from temporary access
challenges without manual intervention.

## Test conditions

The observation was performed:

- from one local machine;
- through one normal network connection;
- without proxy rotation;
- without IP rotation;
- without distributed or parallel request sources;
- without browser fingerprint spoofing;
- without stealth plugins;
- without browser API patching intended to disguise automation;
- without automated CAPTCHA solving;
- without entering personal data;
- without navigating into the booking workflow;
- without reserving or submitting an appointment.

Successful cycles used randomized intervals between 420 and 720 seconds.
Failure states used progressive backoff.

## Observed behaviour

### Direct HTTP observation

Direct HTTP observation was attempted before browser fallback.

Most HTTP attempts were rejected or challenged by the provider-side protection
layer. A limited number of HTTP observations succeeded and returned sufficient
content to classify the state as `NO_SLOTS`.

This shows that direct HTTP access is intermittently available, but not reliable
enough to serve as the only observation method for this provider.

### Playwright fallback

When direct HTTP observation was blocked, the monitor opened the public queue
page through a persistent Playwright browser session.

The browser session remained passive and was used only to read the rendered
queue state.

The fallback did not:

- solve or bypass CAPTCHA;
- alter the browser fingerprint;
- rotate IP addresses;
- create multiple browser identities;
- submit forms;
- enter credentials or personal information;
- reserve an appointment;
- continue into the booking process.

### Queue-state classification

Whenever the queue page was observable, the monitor classified the business
state as `NO_SLOTS`.

One temporary observation-access state was classified as `BLOCKED`.

Page-content changes were detected separately from queue-state changes. Dynamic
page content therefore did not cause false slot-availability notifications.

### Temporary anti-bot challenge

At 2026-07-27 10:03:08, the browser observation changed from:

```text
NO_SLOTS -> BLOCKED
```

The monitor:

- identified the browser-level challenge;
- increased the delay using progressive backoff;
- remained operational;
- did not attempt to evade or solve the challenge.

At 2026-07-27 11:03:56, normal observation recovered automatically:

```text
BLOCKED -> NO_SLOTS
```

The failure streak was reset after recovery.

---

## Stability result

During the observation period:

- no unhandled runtime failure occurred;
- HTTP-to-Playwright fallback remained operational;
- the persistent browser profile remained usable throughout the run;
- randomized observation intervals were applied;
- progressive backoff was applied during the temporary blocked state;
- normal monitoring resumed without manual browser interaction.

The final traceback was caused by manual interruption during the sleep period
after a completed observation cycle. It was not a monitoring failure.

## Findings

### Confirmed

1. Direct HTTP observation is not consistently reliable for the Kortrijk
provider because requests are frequently rejected or challenged.
2. HTTP observation should remain the preferred low-overhead method because it
occasionally succeeds.
3. A passive Playwright fallback is currently necessary to maintain reliable
queue-state observation when direct HTTP access is blocked or challenged.
4. The browser fallback can operate without fingerprint spoofing, proxy
rotation, IP rotation, CAPTCHA solving, or booking automation.
5. The monitor can detect a temporary browser challenge, apply backoff, and
recover without manual intervention.

### Not established by this test

The run did not verify:

- detection of real available slots;
- behaviour during a user-facing CAPTCHA workflow;
- long-term stability beyond approximately 24 hours;
- behaviour from other networks or geographic regions;
- behaviour under multiple concurrent monitor instances;
- whether provider-side anti-bot rules will remain unchanged.

## Decision

For the Kortrijk provider, the observation strategy remains:

```text
direct HTTP observation
        |
        | blocked, challenged, or insufficient
        v
passive Playwright browser observation
```

Playwright is not used to bypass an access challenge. It is used to render the
same public page that a user can open in a normal browser.

When the browser itself is challenged, the monitor records BLOCKED, applies
backoff, and waits. It does not disguise its identity or attempt automated
challenge completion.

## Remaining gaps

- Add graceful KeyboardInterrupt handling.
- Consider separating queue state from observation/access status.
- Define whether diagnostic capture should occur on transition into BLOCKED
or UNKNOWN.
- Run a separate controlled observation with the local Site Investigator.
- Keep diagnostic output, browser profiles, cookies, tokens, and captures
outside the public repository.
