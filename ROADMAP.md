# Roadmap

- [x] Generate standardized, run-scoped Markdown research summaries from
  immutable Observations after long orchestrated monitoring sessions.
- [x] Add a permanent Evidence Matrix and capability-promotion checklist for
  the current deployment trust state.
- [x] Complete the seven-centre 12-hour runtime validation and distinguish
  orchestrator runtime from Observation coverage in generated summaries.
- [x] Complete the six-hour release validation of Berlin, Cologne,
  Bratislava, Toronto, Kortrijk, Madrid, and Barcelona.
- [x] Add the first Architecture Protection CI milestone with existing unit
  tests, compileall, focused boundary/layer guards, and repository hygiene
  checks.
- [x] Implement the governance-authorized SQLite Delivery Job Persistence
  slice with immutable jobs, separate lease/state records, idempotent enqueue,
  priority ordering, bounded retries, and persistence tests.

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
- [x] Confirm Valencia centre `7`, service `4`, public days/times contract,
  and terminal `TIMES` boundary from owner-provided live evidence
- [x] Confirm Berlin centre `2`, service `4`, public days/times contract, and
  the valid terminal `DAYS(1) -> TIMES(0) -> NO_SLOTS` outcome from
  owner-provided live evidence
- [x] Confirm Berlin temporal variability for the same allowed date:
  `TIMES(0) -> NO_SLOTS` followed later by
  `TIMES(9) -> SLOTS_AVAILABLE`
- [x] Confirm Toronto centre `46`, service `4`, public days/times contract,
  one allowed date, and 11 allowed public time entries from `08:15:00` through
  `13:00:00` from owner-provided live evidence
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
- [x] Independently verify Bratislava public discovery contract live
- [x] Start the bounded Berlin/Kortrijk candidate-landing comparison alongside
  the five enabled public-discovery profiles; Berlin evidence was confirmed
  during the run, while Kortrijk remains landing-only
- [x] Capture sanitized Kortrijk candidate form evidence for centre `48`,
  service option `4`, and date/time selectors without selecting the service
- [ ] Confirm Kortrijk service selection and the complete bounded
  `LANDING -> DAYS -> TIMES -> STOP` contract before capability review
- [ ] Analyze time-of-day and cross-centre HTML-change correlations
- [ ] Measure delay from HTML changes to confirmed slot availability
- [ ] Document the manual challenge-intervention flow

## Phase 1 — MVP

- [x] Implement the local Observation, outbox, queue, worker, and runner foundation
- [x] Exclude browser sessions and fingerprinting from MonitorProvider
- [x] Implement evidence-first landing classification and transition guards
- [x] Add typed discovery stages, evidence, and request traces to Observation
- [ ] Validate HTTP session and CSRF handling for each DP Document centre
- [x] Add strict confirmed days/times classifiers used by twelve governed
  evidence profiles
- [ ] Validate or add centre-specific days and times classifiers for the
  remaining centres
- [ ] Add a terminal identity-boundary classifier from live-safe evidence
- [x] Implement separate `MonitorProvider` and reserved `BookingProvider` boundaries
- [x] Integrate Madrid, Barcelona, London, and Milan public `days` and `times`
  discovery into the monitor runtime with a terminal `TIMES` boundary
- [x] Add Valencia as a fifth evidence-gated public-discovery profile for a
  bounded comparative runtime validation
- [x] Admit the evidence-confirmed Berlin, Toronto, Cologne, and Bratislava
  contracts through four explicit governance-reviewed registry changes
- [x] Confirm Prague centre `8`, service `4`, one allowed date, four allowed
  public time entries, and the bounded public discovery contract
- [x] Record the independent Prague governance decision and add `prague-v1`
- [ ] Complete bounded post-promotion runtime validation for Prague
- [x] Confirm Varna centre `43`, service `4`, one allowed date, ten allowed
  time entries, and the bounded public discovery contract through `TIMES`.
- [x] Record the independent Varna governance decision and add `varna-v1`
  through the shared `CityMonitor` entrypoint.
- [ ] Complete bounded post-promotion runtime validation for Varna.
- [x] Confirm Chisinau centre `45`, service `4`, 25 allowed dates, a non-empty
  `TIMES` response, and the bounded public discovery contract.
- [x] Record the independent Chisinau governance decision and add
  `chisinau-v1` through the shared `CityMonitor` entrypoint.
- [ ] Complete bounded post-promotion runtime validation for Chisinau.
- [x] Complete bounded runtime validation of the four newly promoted profiles
- [ ] After the ADR-0009 transition criteria are met, replace city wrappers
  with one registry-driven generic DP Document monitor
- [x] Migrate Kortrijk from its legacy monitor to the shared `CityMonitor`
  landing-only entrypoint and candidate-probe path
- [x] Implement standardized local observation metadata
- [x] Implement separate provider and orchestrator logs
- [ ] Implement subscription and state storage
- [ ] Deduplicate identical monitoring requests
- [ ] Detect availability changes without false `NO_SLOTS` results
- [x] Complete the ADR-0012 documentation milestone:
  - [x] complete conceptual design, architecture review, and governance
    proposal;
  - [x] author proposed ADR-0012;
  - [x] author Notification Architecture, event contracts, configuration
    schema, and notification test strategy;
  - [x] integrate documentation references and release traceability;
  - [x] record governance approval and change ADR-0012 to `Accepted`.
- [x] Implement the first offline notification domain slice after ADR-0012 approval:
  immutable contracts, Policy Set validation, Decision Trace, replay tests,
  and architecture tests
- [x] Implement the separately authorized SQLite Delivery Job Store without a
  worker, adapter, runtime hook, or external delivery
- [ ] Authorize and implement a delivery worker and developer-only Telegram
  adapter only after persistence review
- [ ] Perform bounded notification validation before any runtime integration
- [ ] Review opt-in, retention, deletion, and privacy requirements before
  enabling public notifications or additional delivery channels
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
