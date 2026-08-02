# Seven-centre 12-hour Runtime Validation

**Run ID:** `RUN-20260801-110229-de3587ee`  
**Runtime:** 2026-08-01 13:02:29–2026-08-02 01:05:38 Europe/Amsterdam  
**Runtime duration:** 12h 3m 9s  
**Observation coverage:** 11h 59m 2s  
**Evidence source:** immutable local Observation database and orchestrator log

## Observed facts

- 408 Observations and 408 HTTP attempts were recorded;
- 338 HTTP landing attempts were blocked;
- 308 Playwright executions occurred, including one candidate landing probe;
- 307 discovery executions reached `TIMES`, and all 307 stopped there;
- no browser error, unexpected browser `UNKNOWN`, CAPTCHA interaction,
  identity interaction, or booking action was recorded;
- Madrid, London, Milan, Barcelona, and Valencia completed every invoked
  bounded fallback discovery;
- Berlin produced one bounded candidate landing artifact and then respected
  candidate-probe cooldown;
- Kortrijk produced two recognized HTTP `200` landing-level `NO_SLOTS`
  observations and 16 blocked observations. Its legacy entrypoint did not
  execute the shared candidate probe during this historical run.

## Timing correction

The original automatic summary was skipped because the generator measured the
interval between first and last Observation (11.98h), not orchestrator runtime.
The orchestrator actually ran for 12h 3m 9s. The generator now reports runtime
duration and Observation coverage separately and uses runtime duration for the
minimum-run threshold.

## Interpretation

Within this run and the five enabled discovery profiles, the experimental
Playwright transport reliably recovered bounded public availability after HTTP
blocking. The result does not establish equivalent reliability or protocol
details for unreviewed deployments.

## Boundary

No committed research artifact contains cookies, browser storage, CSRF values,
raw HTML, HAR, screenshots, identity data, or booking data. The generated full
report remains local and Git-ignored.
