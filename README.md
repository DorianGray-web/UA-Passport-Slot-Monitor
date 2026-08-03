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
- remains HTTP-first for DP Document queue discovery;
- permits an explicitly enabled, bounded Playwright transport only for
  evidence-confirmed research profiles after HTTP is blocked;
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
implemented. Twelve governance-approved, evidence-gated profiles—Madrid,
Barcelona, London, Milan, Valencia, Berlin, Toronto, Cologne, Bratislava, and
Prague, plus Varna and Chisinau—run through public `DAYS` and `TIMES` and stop.
Kortrijk remains landing-only.

Across the currently evidence-confirmed deployments, successful HTTP `200`
landing responses exposed the public queue form and public discovery could
proceed through `DAYS` and `TIMES`. This is an observed evidence set, not a
protocol guarantee for other or future deployments.

The current evidence set contains twelve independently reviewed deployments.
Berlin demonstrates both `TIMES(0) -> NO_SLOTS` and, later for the same date,
`TIMES(9) -> SLOTS_AVAILABLE`: the public stage sequence remained stable while
the availability payload changed.

A six-hour release validation completed on 2026-08-02 for Berlin, Cologne,
Bratislava, Toronto, Kortrijk, Madrid, and Barcelona. The four newly governed
profiles completed bounded browser discovery without browser errors or
browser `UNKNOWN`. Cologne remained `NO_SLOTS` throughout this window;
Kortrijk produced no candidate identifiers during that historical window.
A later bounded candidate probe detected the public queue form, centre `48`,
service option `4`, and date/time selectors, but did not select the service or
execute `DAYS` or `TIMES`; Kortrijk therefore remains landing-only.

Still planned:

- full runtime integration for the remaining centres;
- live validation for the remaining centre-specific contracts;
- an operator-facing blocked/challenge workflow;
- the evidence-first notification Output Pipeline described by proposed
  ADR-0012;
- Telegram and email delivery adapters after notification governance,
  offline contracts, replay tests, and bounded validation.

## Recommended Reading Order

The repository documentation is organized by responsibility rather than by
chronological development. For first-time readers, the recommended order is:

1. **README** — understand the project's purpose, principles, and current
   scope.
2. **[Evidence Matrix](docs/EVIDENCE_MATRIX.md)** — review the current trust
   state, deployment maturity, and governance status.
3. **[Architecture](docs/ARCHITECTURE.md)** — learn how trusted capabilities
   are implemented and guarded at runtime.
4. **[Project Decisions](docs/DECISIONS.md)** — understand why the governing
   architectural rules exist.
5. **[Research Notes](research/README.md)** — review the retained evidence
   supporting individual capability decisions.

This order separates mission, current trust state, implementation, rationale,
and evidence. Historical plans and reports remain valuable records, but they
are not the primary description of current runtime behaviour.

## Project documentation

- [Project Concept](docs/PROJECT_CONCEPT.md)
- [Roadmap](ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Decisions](docs/DECISIONS.md)
- [Evidence Matrix](docs/EVIDENCE_MATRIX.md)
- [Notification Architecture](docs/NOTIFICATION_ARCHITECTURE.md)
- [Notification Event Contracts](docs/contracts/notification-events.md)
- [Notification Test Strategy](docs/testing/notification-test-strategy.md)
- [Release Policy](docs/RELEASE_POLICY.md)
- [v0.3.0 Release Readiness Report](docs/releases/2026-08-02-v0.3.0-release-readiness.md)
- [Providers](docs/PROVIDERS.md)
- [User Flow](docs/USER_FLOW.md)
- [Research](research/README.md)
- [Privacy](PRIVACY.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Documentation Language Policy](docs/LANGUAGE_POLICY.md)

### Research summary reports

When `monitor_runner.py` is stopped with `Ctrl+C` or reaches a configured
bounded-run deadline, it automatically generates a local Markdown summary for
runs lasting at least one hour. Runtime duration and Observation coverage are
reported separately. Reports are written to
`research/dp-document/<date>-playwright-fallback-<hours>h-report.md` and are
built exclusively from immutable Observations in `data/observations.sqlite3`.
Generated reports are runtime output and are ignored by Git; only manually
reviewed, sanitized conclusions belong in committed research documentation.

Generate or regenerate a report manually with:

```powershell
.\.venv-2\Scripts\python.exe .\research\dp-document\tools\generate_research_summary.py --run-id RUN-...
```

Use `--force` for a deliberately short validation run. Automatic generation
can be disabled with `RESEARCH_SUMMARY_ENABLED=false`; its duration threshold
can be changed with `RESEARCH_SUMMARY_MINIMUM_HOURS`.

Localized user documentation:
[Русский](docs/ru/README.md) · [Українська](docs/uk/README.md)

## Running the local provider monitors

Create an environment and install dependencies.

The runner starts every entry in `providers/dp-document/providers.json` whose
`enabled` field is `true`. The current research sample contains thirteen centres:
Kortrijk, Berlin, Bratislava, Madrid, London, Milan, Toronto, Chisinau,
Barcelona, Valencia, Cologne, Prague, and Varna.

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

Each provider remains a separate process. Provider activity is written to
`logs/<city>.log` and its analysis mirror to `metadata/<city>.jsonl`. Runner
lifecycle events are written to `logs/orchestrator.log`. A separately
supervised diagnostic worker drains the persistent priority queue and writes
`logs/diagnostic-worker.log`.

Each registry entry also carries a research `priority` and
`observation_group` (`active` or `control`). These fields describe the
research sample; they do not alter classifier behavior, polling frequency, or
diagnostic queue priority.

`startup_delay_seconds` staggers the first request from each provider.
Repeated HTTP blocking continues to use exponential backoff and, after four
consecutive `BLOCKED` observations, a minimum cooldown controlled by
`BLOCKED_COOLDOWN_SECONDS` (default: 3600 seconds).

For a temporary research cohort, set `MONITOR_PROVIDER_CITIES` to a
comma-separated list. The registry is not modified:

```powershell
$env:MONITOR_PROVIDER_CITIES = "madrid,london,milan"
python.exe .\monitor_runner.py
```

Set `MONITOR_RUN_DURATION_SECONDS` for an automatically completed bounded run.
The orchestrator stops its children cleanly and generates the research summary
at the deadline.

For a bounded four-centre transport experiment, explicitly enable the
persistent browser fallback:

```powershell
$env:MONITOR_PROVIDER_CITIES = "madrid,barcelona,london,milan"
$env:PLAYWRIGHT_DISCOVERY_FALLBACK_ENABLED = "true"
.\.venv-2\Scripts\python.exe .\monitor_runner.py
```

For an explicitly selected confirmed-profile comparison run:

```powershell
$env:MONITOR_PROVIDER_CITIES = "madrid,barcelona,london,milan,valencia,berlin,toronto,cologne,bratislava"
$env:PLAYWRIGHT_DISCOVERY_FALLBACK_ENABLED = "true"
$env:RESEARCH_SUMMARY_MINIMUM_HOURS = "3"
.\.venv-2\Scripts\python.exe .\monitor_runner.py
```

HTTP is attempted first on every cycle. Playwright starts only after
`BLOCKED`, uses separate local profiles under `.browser-data/`, and stops at
public `TIMES`. It does not interact with CAPTCHA, identity, or booking.

The 2026-08-01 seven-centre research run originally treated Berlin and
Kortrijk as candidate landing probes. Berlin's public discovery contract was
subsequently confirmed by live review and promoted through explicit
governance; Kortrijk remains candidate-only. The historical command remains a
record of that earlier evidence state:

```powershell
$env:MONITOR_PROVIDER_CITIES = "madrid,barcelona,london,milan,valencia,berlin,kortrijk"
$env:PLAYWRIGHT_DISCOVERY_FALLBACK_ENABLED = "true"
$env:CANDIDATE_EVIDENCE_PROBE_ENABLED = "true"
$env:CANDIDATE_EVIDENCE_PROBE_COOLDOWN_SECONDS = "21600"
$env:RESEARCH_SUMMARY_MINIMUM_HOURS = "3"
.\.venv-2\Scripts\python.exe .\monitor_runner.py
```

Sanitized candidate form details are written only under Git-ignored
`research-output/candidate-evidence/<city>/`. Candidate evidence cannot enable
a discovery profile; an explicit governance review and registry change are
required.

Every check stores an immutable, schema-versioned Observation in
`data/observations.sqlite3`. The transaction also stores its diagnostic
decision and, when accepted, an outbox command. Per-provider
`metadata/<city>.jsonl` files remain disposable analysis mirrors.
`data/diagnostic-queue.sqlite3` stores queued jobs, leases, and safe results.
Runtime databases, logs, metadata, browser profiles, page captures, and state
files are ignored by Git.

These entry points are local research/prototyping tools. They do not send
Telegram or email notifications and they do not book appointments.

ADR-0012 is `Accepted`. The first offline notification-domain slice implements
only immutable contracts, fail-closed Policy Set loading, append-only Decision
Traces, and pure replay tests. A separately authorized persistence slice adds
immutable Delivery Jobs and local SQLite job/state storage. No notification
Coordinator, worker, delivery adapter, subscription store, Telegram
integration, runtime hook, Observation reader, or external message exists.

## Architecture protection checks

GitHub Actions runs the existing `unittest` suite, compiles Python sources,
and executes focused static guards for protected imports, future notification
layer direction, tracked runtime artifacts, and high-confidence committed
secrets. The same architecture checks can be run locally:

```powershell
python -m tools.architecture.check_boundaries
python -m tools.architecture.check_layer_direction
python -m tools.architecture.check_hygiene
```

The notification checks validate the offline `notifications/` package and
protect ADR-0011 and accepted ADR-0012 boundaries. They do not authorize
delivery infrastructure or runtime integration.

## Contributing

Ideas, real-world use cases, documentation improvements, testing, security reviews, and code contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.
