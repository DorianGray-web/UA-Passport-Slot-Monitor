# Notification Channels

> Status: Historical channel research; superseded for architecture by
> [ADR-0012](DECISIONS.md#adr-0012-evidence-first-notification-derivation-and-output-isolation)
> and [Notification Architecture](NOTIFICATION_ARCHITECTURE.md).

## Purpose

This document describes the notification requirements and candidate delivery channels for UA Passport Slot Monitor.

This document retains the early delivery-channel comparison. Telegram is now
the first planned, replaceable adapter in the accepted architecture. ADR-0012
is `Accepted`, but no delivery channel is implemented.

No notification sender is currently implemented. Diagnostic decisions and
outbox commands belong to the diagnostic subsystem and must not be described
as user notifications.

## Core requirements

- fast delivery;
- clear indication of the relevant centre and service;
- no passport or booking data in notifications;
- user-controlled opt-in and opt-out;
- minimal storage of contact information;
- protection of tokens and notification credentials;
- support for provider replacement without changing monitoring logic.

## Candidate channels

### Email

Advantages:

- broadly available;
- no additional application required;
- suitable as a fallback channel.

Limitations:

- delivery or user response may be slower;
- messages may be filtered as spam.

### Telegram

Advantages:

- fast delivery;
- comparatively simple bot integration;
- low implementation cost.

Limitations:

- requires a Telegram account;
- bot identifiers must be stored securely;
- not preferred by every user group.

### WhatsApp

Advantages:

- broad adoption among non-technical users;
- high visibility of notifications.

Limitations:

- Business Platform requirements;
- possible usage costs;
- template and provider restrictions;
- greater implementation and compliance complexity.

### Web Push

Advantages:

- no messaging account required;
- direct browser notifications;
- potentially privacy-preserving.

Limitations:

- browser and platform restrictions;
- permission management;
- inconsistent background delivery, especially on mobile platforms.

## Supersession note — 2026-08-03

The normative proposal now defines a transport-independent, one-way Output
Pipeline. Telegram is the first planned adapter, not a runtime dependency or
an implemented sender. Channel implementation remains blocked on governance
acceptance, offline domain contracts, replay tests, privacy validation, and
bounded validation. This historical comparison remains useful input and does
not authorize implementation.

## Notification content

Notifications should contain only the minimum useful information:

- centre;
- service;
- detected availability state;
- detection time;
- link to the official service.

Notifications must not contain:

- passport numbers;
- identity-document data;
- CAPTCHA information;
- passwords or session tokens;
- booking confirmation data.

## Future updates

Future channel research should be recorded here when:

- survey results are available;
- an MVP notification channel is selected;
- another provider is added;
- operating costs or provider restrictions change.
