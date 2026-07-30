# User Flow

## Current local prototype

An operator configures environment variables and starts `python -m
monitor_runner`. Three independent processes inspect provider landing pages,
store immutable Observations, and may create diagnostic work through the
outbox and queue. No end-user UI, subscription flow, Telegram integration, or
booking flow is implemented.

## Proposed end-user flow

The future service may let a user select a location, centre, service, and
number of applicants, then create a monitoring subscription and choose a
notification channel. This is product design, not current behavior. See
[Project Concept](PROJECT_CONCEPT.md) and [Notification Research](NOTIFICATIONS.md).
