# Roadmap

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
- [ ] Confirm live availability data for days and time slots
- [ ] Determine stable HTTP session requirements for each centre
- [x] Define the initial normalized monitoring metadata model
- [x] Record user-provided Bratislava and Milan evidence supporting separate
  date and time discovery stages
- [x] Establish responsible polling and bounded backoff rules
- [x] Add offline-validated Berlin and Bratislava monitor entrypoints
- [x] Add concurrent multi-provider process supervision
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
- [ ] Add explicit days and times response classifiers from live-safe fixtures
- [x] Implement separate `MonitorProvider` and reserved `BookingProvider` boundaries
- [ ] Integrate the HTTP `days` and `times` methods into the monitor runtime
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
