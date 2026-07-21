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
- [ ] Determine stable session requirements
- [ ] Define the normalized provider response model
- [ ] Establish responsible polling and backoff rules
- [ ] Document the manual challenge-intervention flow

## Phase 1 — MVP

- [ ] Implement the core architecture
- [ ] Implement browser-session management
- [ ] Implement the provider abstraction
- [ ] Implement the first Kortrijk provider adapter
- [ ] Implement subscription and state storage
- [ ] Deduplicate identical monitoring requests
- [ ] Detect availability changes without false `NO_SLOTS` results
- [ ] Implement Telegram and email notifications
- [ ] Implement the manual CAPTCHA workflow
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
