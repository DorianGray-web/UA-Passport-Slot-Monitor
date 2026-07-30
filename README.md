# UA Passport Slot Monitor

A privacy-focused open-source service for monitoring appointment availability at Ukrainian document service centers abroad.

> 🚧 **Current status:** Research and provider-integration prototyping. Local
> monitoring and diagnostic infrastructure exists, but it is not a
> production-ready notification service.

## Why this project exists

Appointment slots for Ukrainian passport and document services abroad may remain unavailable for weeks and then appear only briefly.

UA Passport Slot Monitor aims to notify users when availability changes, without automatically booking appointments or bypassing CAPTCHA.

## We need your feedback

Please take 2 minutes to complete our **[User Survey](https://forms.gle/yXTAV1aAEh8Z84zN6)** and help us prioritize the features that matter most to future users.

Feedback from users, developers, security specialists, UX designers, and open-source contributors is welcome.

## Core principles

- no automatic appointment booking;
- does not automatically solve CAPTCHA or programmatically bypass anti-bot
  challenges;
- does not rotate proxies, IP addresses, or browser identities;
- uses HTTP for normal DP Document queue discovery;
- reserves browser automation for separate diagnostics and controlled research;
- no passport-number collection;
- privacy-first location handling;
- responsible request rates;
- shared checks for identical subscriptions where possible;
- manual completion of final registration;
- uncertain, blocked, or incomplete responses are never reported as `NO_SLOTS`.

## Current status

The project has completed its initial conceptual and documentation foundation and has moved into provider feasibility research.

The first technical study uses the DP Document service center in Kortrijk,
Belgium. Analysis of frontend 7.34.2 has confirmed that:

- pre-authentication discovery uses HTTP `form=days` and `form=times` requests;
- those requests require service centre, service, CSRF, and date where
  applicable, but no browser fingerprint;
- embedded ThumbmarkJS fingerprinting belongs only to booking submission;
- challenge pages, CAPTCHA, access restrictions, and incomplete captures must be detected separately from valid availability responses.

The HTTP `MonitorProvider` boundary and its `days`/`times` request methods are
implemented. The current Kortrijk, Berlin, and Bratislava monitor processes
classify the landing response only; they do not yet run or normalize the full
`days`/`times` discovery flow. That flow and every centre still require
authorized live validation.

Still planned:

- one document center;
- one document service;
- full runtime integration of HTTP session, CSRF, `days`, and `times`;
- live-validated availability-state detection;
- safe polling and backoff rules;
- an operator-facing blocked/challenge workflow;
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

## Running the local provider monitors

Create an environment and install dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m monitor_runner
```

On Linux or macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m monitor_runner
```

Each provider remains a separate process. A separately supervised diagnostic
worker drains the persistent priority queue. Provider activity is written to
`logs/kortrijk.log`, `logs/berlin.log`, and `logs/bratislava.log`; runner
lifecycle events are written to `logs/orchestrator.log`, and worker events to
`logs/diagnostic-worker.log`.

Every check stores an immutable, schema-versioned Observation in
`data/observations.sqlite3`. The transaction also stores its diagnostic
decision and, when accepted, an outbox command. Per-provider
`metadata/<city>.jsonl` files remain disposable analysis mirrors.
`data/diagnostic-queue.sqlite3` stores queued jobs, leases, and safe results.
Runtime databases, logs, metadata, browser profiles, page captures, and state
files are ignored by Git.

These entry points are local research/prototyping tools. They do not send
Telegram or email notifications and they do not book appointments.

## Contributing

Ideas, real-world use cases, documentation improvements, testing, security reviews, and code contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.
