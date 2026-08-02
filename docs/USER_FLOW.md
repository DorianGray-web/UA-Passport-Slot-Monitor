# User Flow

## Current local prototype

An operator configures environment variables and starts `python -m
monitor_runner`. The orchestrator loads `providers.json` and supervises twelve
independent provider processes plus the diagnostic worker. Each `CityMonitor`
selects HTTP first; an explicitly enabled confirmed profile may use bounded
Playwright after HTTP is blocked. The Runtime Guard stops discovery at
`TIMES`, and every cycle stores an immutable transport-independent
Observation. No end-user UI, subscription flow, Telegram integration, or
booking flow is implemented.

## Proposed end-user flow

The future service may let a user select a location, centre, service, and
number of applicants, then create a monitoring subscription and choose a
notification channel. This is product design, not current behavior. See
[Project Concept](PROJECT_CONCEPT.md) and [Notification Research](NOTIFICATIONS.md).
