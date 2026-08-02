# Seven-centre Six-hour Release Validation

**Run ID:** `RUN-20260801-234419-release-validation`  
**Runtime:** 2026-08-02 01:44:30–07:44:30 Europe/Amsterdam  
**Runtime duration:** 6h 0m  
**Observation coverage:** 5h 57m  
**Evidence source:** immutable local Observations, orchestrator logs, and
owner-provided visual confirmation identified below

## Scope

The bounded run compared four newly governed profiles (Berlin, Cologne,
Bratislava, and Toronto), two established controls (Madrid and Barcelona), and
the landing-only Kortrijk candidate probe. HTTP remained first in every cycle.
Playwright was explicitly enabled for this research run and remained bounded
by the confirmed public discovery contract.

## Observed facts

- the orchestrator completed its configured 21,600-second runtime and stopped
  all seven provider processes and the diagnostic worker cleanly;
- 241 Observations and 241 HTTP landing attempts were recorded;
- 213 HTTP attempts returned `403`; the remaining 28 returned `200`;
- HTTP alone reached `TIMES` in zero cycles;
- confirmed Playwright discovery ran 202 times: 117 executions reached
  `TIMES`, while 85 terminated earlier in a recognized `NO_SLOTS` state;
- the separate Kortrijk candidate landing probe ran once and stopped at
  `LANDING` without detecting a queue form, service selector, or service
  options;
- no Playwright `UNKNOWN`, browser error, CAPTCHA interaction, identity-data
  interaction, or booking action was recorded;
- Madrid remained `SLOTS_AVAILABLE` in 33 browser cycles with 11 dates and
  229–230 available time entries;
- Barcelona remained `SLOTS_AVAILABLE` in 30 browser cycles with 12 dates and
  326–329 available time entries;
- Berlin changed from `NO_SLOTS` to `SLOTS_AVAILABLE`; its available time-entry
  count later declined from nine to four while the confirmed stage contract
  remained unchanged;
- Bratislava changed from `NO_SLOTS` to `SLOTS_AVAILABLE` and repeatedly
  exposed one date and nine available time entries;
- Toronto changed from `NO_SLOTS` to `SLOTS_AVAILABLE` for seven cycles, with
  one date and up to 30 available time entries, then returned to `NO_SLOTS`;
- Cologne produced 38 `NO_SLOTS` observations and no available date or time
  entry during this run;
- Kortrijk produced three recognized `NO_SLOTS` observations and ten
  `BLOCKED` observations. It produced no candidate identifiers and remains
  landing-only.

## Owner-provided visual confirmation

During the validation window, the project owner visually confirmed current
`NO_SLOTS` pages for Berlin and Kortrijk. This is user-provided live evidence,
kept distinct from repository-derived implementation evidence and immutable
runtime Observations. The screenshots remain local and are not committed.

## Interpretation

Within this observation window, every invoked confirmed browser-discovery path
either reached `TIMES` or stopped at a recognized earlier `NO_SLOTS` boundary.
The absence of a `TIMES` transition is therefore not automatically a transport
failure.

Cologne's zero-slot result does not contradict its earlier live review, which
confirmed the public contract and available time entries at a different
moment. It supports the narrower interpretation that Cologne availability may
be short-lived and was not present during this six-hour sample.

Kortrijk yielded no new public-contract evidence. Its candidate probe result
does not justify a service identifier, discovery profile, or capability
promotion. Subsequent bounded observation may add evidence, but governance
state remains unchanged until reviewed evidence exists.

## Boundary

All confirmed discovery stopped no later than `TIMES`. The candidate probe
stopped at `LANDING`. No runtime path submitted personal information,
interacted with CAPTCHA, attempted identity verification, or performed a
booking action. Raw runtime reports, browser profiles, logs, metadata, and
screenshots remain local and Git-ignored.

