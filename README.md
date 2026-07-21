# UA Passport Slot Monitor

A privacy-focused open-source service for monitoring appointment availability at Ukrainian document service centers abroad.

> 🚧 **Current status:** Research, user validation, and provider integration prototyping. No production implementation is available yet.

## Why this project exists

Appointment slots for Ukrainian passport and document services abroad may remain unavailable for weeks and then appear only briefly.

UA Passport Slot Monitor aims to notify users when availability changes, without automatically booking appointments or bypassing CAPTCHA.

## We need your feedback

Please take 2 minutes to complete our **[User Survey](https://forms.gle/yXTAV1aAEh8Z84zN6)** and help us prioritize the features that matter most to future users.

Feedback from users, developers, security specialists, UX designers, and open-source contributors is welcome.

## Core principles

- no automatic appointment booking;
- no CAPTCHA or Cloudflare bypass;
- no passport-number collection;
- privacy-first location handling;
- responsible request rates;
- shared checks for identical subscriptions where possible;
- manual completion of final registration;
- uncertain, blocked, or incomplete responses are never reported as `NO_SLOTS`.

## Current status

The project has completed its initial conceptual and documentation foundation and has moved into provider feasibility research.

The first technical study uses the DP Document service center in Kortrijk, Belgium. Research has confirmed that:

- direct HTTP access may be rejected while the public appointment application remains accessible in a normal browser session;
- the public client application exposes the general appointment flow from service selection to available days, available times, and manual registration;
- challenge pages, CAPTCHA, access restrictions, and incomplete captures must be detected separately from valid availability responses.

Live availability data has not yet been confirmed or normalized, and the first provider adapter has not yet been implemented.

Initial development will focus on:

- one document center;
- one document service;
- browser-session management;
- reliable availability-state detection;
- safe polling and backoff rules;
- manual CAPTCHA handling;
- Telegram and email notifications.

## Project documentation

- [Project Concept](docs/PROJECT_CONCEPT.md)
- [Roadmap](ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Decisions](docs/DECISIONS.md)
- [Providers](docs/PROVIDERS.md)
- [User Flow](docs/USER_FLOW.md)
- [Research](research/README.md)
- [Privacy](PRIVACY.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Documentation Language Policy](docs/LANGUAGE_POLICY.md)

Localized user documentation:
[Русский](docs/ru/README.md) · [Українська](docs/uk/README.md)

## Contributing

Ideas, real-world use cases, documentation improvements, testing, security reviews, and code contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.
