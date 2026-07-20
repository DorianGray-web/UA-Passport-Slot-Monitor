# Notification Channels

> Status: Research and validation

## Purpose

This document describes the notification requirements and candidate delivery channels for UA Passport Slot Monitor.

No final notification provider has been selected yet. The initial implementation decision will be based on user survey results, technical feasibility, privacy, reliability, and operating cost.

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

## Current decision

The project will not select a primary notification provider until the current user survey has been reviewed.

The notification layer should be modular so that one or more channels can be added without changing the provider-monitoring logic.

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

This document will be updated when:

- survey results are available;
- an MVP notification channel is selected;
- another provider is added;
- operating costs or provider restrictions change.
