# Roadmap

- [x] Generate standardized, run-scoped Markdown research summaries from
  immutable Observations after long orchestrated monitoring sessions.

## Phase 0 — Foundation and Validation

- [x] Define the problem and initial project scope
- [x] Adopt privacy and security policies
- [x] Publish the initial documentation foundation
- [x] Launch the user survey
- [x] Collect initial public feedback
- [x] Select the first provider location for technical research

## Phase 0.5 — Provider Feasibility Research

- [x] Verify access to the public appointment page through a normal browser session
- [x] Identify access-restriction, CAPTCHA, and challenge-page states
- [x] Confirm that the general appointment workflow can be observed
- [x] Define capture validation as a required processing step
- [x] Confirm Madrid live availability response schemas for days and time
  slots
- [x] Confirm Barcelona public days/times request and response contracts
- [x] Confirm live availability schemas for the additional London and Milan
  research profiles
- [ ] Confirm live availability schemas for the remaining configured centres
- [ ] Capture sanitized days, times, and first identity-boundary fixtures
- [ ] Determine whether a public appointment count is exposed
- [ ] Determine stable HTTP session requirements for each centre
- [x] Define the initial normalized monitoring metadata model
- [x] Record user-provided Bratislava and Milan evidence supporting separate
  date and time discovery stages
- [x] Establish responsible polling and bounded backoff rules
- [x] Add offline-validated Berlin and Bratislava monitor entrypoints
- [x] Add concurrent multi-provider process supervision
- [x] Add configuration-driven eight-centre research supervision
- [x] Expand supervision to the evidence-confirmed ninth centre, Barcelona
- [x] Add an opt-in Madrid, Barcelona, London, and Milan persistent-browser
  discovery experiment
- [x] Analyze a bounded four-centre, three-hour-57-minute HTTP/Playwright
  comparison run (`79/79` fallback discoveries reached `TIMES`)
- [x] Add research priority and active/control sample groups
- [x] Complete an approximately eight-hour Madrid, London, and Milan HTTP
  runtime validation without process failures
- [x] Confirm stable event-driven suppression of repeated unchanged
  `BLOCKED` diagnostics
- [x] Confirm that HTTP monitoring can intermittently reach unrecognized
  public queue forms for Madrid and Milan
- [x] Define Observation as the immutable source-of-truth event
- [x] Add transactional diagnostic decisions and outbox delivery
- [x] Add backend-agnostic queue, dispatcher, and diagnostic worker contracts
- [x] Add SQLite priority, cooldown, deduplication, and lease recovery
- [ ] Independently verify Berlin and Bratislava monitor classification live
- [ ] Analyze time-of-day and cross-centre HTML-change correlations
- [ ] Measure delay from HTML changes to confirmed slot availability
- [ ] Document the manual challenge-intervention flow

## Phase 1 — MVP

- [x] Implement the local Observation, outbox, queue, worker, and runner foundation
- [x] Exclude browser sessions and fingerprinting from MonitorProvider
- [x] Implement evidence-first landing classification and transition guards
- [x] Add typed discovery stages, evidence, and request traces to Observation
- [ ] Validate HTTP session and CSRF handling for each DP Document centre
- [x] Add strict confirmed days/times classifiers used by the Madrid,
  Barcelona, London, and Milan evidence profiles
- [ ] Validate or add centre-specific days and times classifiers for the
  remaining centres
- [ ] Add a terminal identity-boundary classifier from live-safe evidence
- [x] Implement separate `MonitorProvider` and reserved `BookingProvider` boundaries
- [x] Integrate Madrid, Barcelona, London, and Milan public `days` and `times`
  discovery into the monitor runtime with a terminal `TIMES` boundary
- [ ] After the ADR-0009 transition criteria are met, replace city wrappers
  with one registry-driven generic DP Document monitor
- [x] Implement the initial Kortrijk observation adapter
- [x] Implement standardized local observation metadata
- [x] Implement separate provider and orchestrator logs
- [ ] Implement subscription and state storage
- [ ] Deduplicate identical monitoring requests
- [ ] Detect availability changes without false `NO_SLOTS` results
- [ ] Implement Telegram and email notifications
- [ ] Implement an operator-facing blocked/challenge workflow
- [ ] Test notifications using real availability changes

## Phase 2 — Public Beta

- [ ] Onboard the first public users
- [ ] Measure reliability and provider load
- [ ] Improve performance and resilience
- [ ] Collect structured user feedback
- [ ] Fix beta defects

## Phase 3 — Ecosystem

- [ ] Add providers only after separate feasibility and policy review
- [ ] Evaluate a browser extension
- [ ] Grow the contributor community
- [ ] Expand documentation translations

## Phase 4 — Collaboration

- [ ] Communicate with official service providers
- [ ] Collect technical and operational feedback
- [ ] Explore official integration opportunities
- [ ] Prefer official APIs when available
