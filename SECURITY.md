# Security Policy

> **Status: Draft**
>
> UA Passport Slot Monitor is currently in the design and validation stage.
> No production deployment exists yet. This policy defines how security
> issues should be reported and handled now, and will be expanded with
> operational details (on-call contact, disclosure timelines, bug bounty
> status) as the project moves toward a public production release.

## 1. Project scope and threat model

UA Passport Slot Monitor monitors public appointment-availability pages of
Ukrainian document service centers abroad and notifies users of changes. It
does not automatically book appointments and does not solve CAPTCHA or
bypass Cloudflare or similar bot-protection systems (see `PROJECT_CONCEPT.md`
and `PRIVACY.md`).

Because of this, the project's security posture concerns two things equally:

- protecting **this project's own code, infrastructure, and any data it
  processes** (see §3, in scope);
- **not becoming a tool that harms the official services it monitors** — for
  example by evading their protections, overloading their infrastructure, or
  enabling unauthorized automated booking (see §4, out of scope).

## 2. Reporting a vulnerability

Please report suspected security vulnerabilities **privately**, not through a
public GitHub issue.

Preferred channel:

- Use GitHub's **[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)**
  feature on this repository (**Security → Report a vulnerability**), if
  enabled for this project.

If private reporting is not available or you prefer email, use the contact
method listed in the repository's profile/README. *(A dedicated security
contact address will be published here once the project has a maintainer
team beyond a single author; until then, GitHub's private reporting flow is
the primary channel.)*

Please do not disclose the issue publicly (including in GitHub Issues,
Discussions, or social media) until it has been reviewed and, where
applicable, fixed.

### What to include

To help triage the report quickly, please include where possible:

- a clear description of the vulnerability and its potential impact;
- steps to reproduce, or a proof-of-concept;
- affected file(s), endpoint(s), or component(s);
- any relevant logs or screenshots, **with personal data and secrets
  redacted**.

Do not include real passport numbers, personal identification data,
credentials, session cookies, API keys, or access tokens in a report — see
`PRIVACY.md` for the categories of data this project must never handle.

## 3. In scope

Security reports about this project's own code and design are welcome,
including but not limited to:

- vulnerabilities in this repository's source code (once implementation
  begins);
- insecure handling of secrets, tokens, or session data described in
  `PRIVACY.md`;
- authentication, authorization, or session-management flaws in the
  project's own application or notification pipeline;
- dependency vulnerabilities with a realistic impact on this project;
- design flaws that could cause the project to collect or retain more
  personal data than described in `PRIVACY.md`;
- design flaws that could cause the project to send excessive or abusive
  request volume to a monitored third-party site.

## 4. Out of scope

The following are explicitly **not** appropriate security reports for this
project, because they conflict with its stated principles
(`PROJECT_CONCEPT.md`, §10 "Responsible use"):

- techniques for bypassing CAPTCHA or Cloudflare/anti-bot protection on
  monitored document-service websites;
- techniques for automating final appointment booking;
- vulnerabilities in the third-party government or document-center websites
  themselves — these should be reported directly to the operator of that
  service, not to this project;
- rate-limiting or scraping "improvements" intended to circumvent a
  monitored service's request limits.

Submissions of this kind will be declined regardless of technical merit,
since implementing them would violate the project's core principles.

## 5. Response process

As an early-stage, primarily single-maintainer open-source project, there is
currently no formal SLA. As a best-effort target:

- an initial acknowledgement will be attempted within a reasonable time
  after a report is received;
- the reporter will be kept informed of progress where possible;
- a fix or mitigation will be prioritized according to severity and impact;
- credit will be offered to the reporter (if desired) once an issue is
  resolved and disclosure is coordinated.

This process will be formalized (response-time targets, severity
classification) before the project reaches a public production release.

## 6. Supported versions

The project has not yet published a release. There is currently no version
support table; the `main` branch is the only supported state. This section
will be updated once tagged releases exist.

## 7. Related documents

- [`PRIVACY.md`](./PRIVACY.md) — what personal data the project does and does
  not process, and how it should be protected.
- [`PROJECT_CONCEPT.md`](./docs/PROJECT_CONCEPT.md) — the project's responsible-use
  principles, including the CAPTCHA/Cloudflare and no-auto-booking
  commitments referenced above.
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — general contribution guidelines,
  including the responsible-development constraints for pull requests.

## 8. Changes to this policy

This policy will evolve as the project moves from design to implementation
and production deployment. Material changes should be documented in the
repository history and, where relevant, in `CHANGELOG.md`.

## 9. Responsible disclosure

The project appreciates responsible security research.

Security researchers acting in good faith, respecting applicable laws and the project's principles, are welcome to report vulnerabilities through the responsible disclosure process described above.

**Last updated:** 2026-07-20
