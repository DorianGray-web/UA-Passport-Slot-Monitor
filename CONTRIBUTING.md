# Contributing to UA Passport Slot Monitor

Thank you for your interest in the project.

UA Passport Slot Monitor is in research and provider-integration prototyping.
Local monitor and diagnostic infrastructure exists, but subscriptions,
notifications, booking, and production operation do not. Contributions do not
need to include code.

## Ways to contribute

You can help by:

- sharing a real-world appointment-booking experience;
- suggesting features or notification channels;
- reviewing the proposed architecture;
- identifying privacy or security risks;
- improving documentation;
- researching document service providers;
- testing future implementations;
- contributing code.

## Before opening an issue

Please check the existing documentation:

- [Project Concept](docs/PROJECT_CONCEPT.md)
- [Roadmap](ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Privacy](PRIVACY.md)
- [Security](SECURITY.md)

Use the following authority order when documents appear to disagree:

1. code, tests, configuration, and runtime contracts for implemented behavior;
2. [Architecture](docs/ARCHITECTURE.md), [Provider Support](docs/PROVIDERS.md),
   [Security](SECURITY.md), and [Privacy](PRIVACY.md) for current boundaries;
3. [Project Decisions](docs/DECISIONS.md) for accepted or superseded choices;
4. dated specifications, plans, and verification reports for their stated
   scope and time;
5. [Project Concept](docs/PROJECT_CONCEPT.md) and
   [Notification Research](docs/NOTIFICATIONS.md) for planned product behavior.

Historical research and verification evidence must not be silently rewritten
when architecture changes. Add a supersession note and link to the current
decision instead.

## Reporting ideas and problems

When opening an issue, please include:

- the country and document center, when relevant;
- the document service involved;
- the observed website behaviour;
- whether CAPTCHA or rate limiting appeared;
- the expected result;
- screenshots with all personal data removed.

Never publish passport numbers, personal identification data, appointment confirmation codes, session cookies, authentication data, API keys, or access tokens.

## Code contributions

Before starting a large implementation:

1. Open an issue describing the proposed change.
2. Explain the problem it solves.
3. Discuss the proposed approach before implementation.
4. Keep the pull request focused on one change.
5. Add or update tests and documentation where applicable.

## Responsible development

Contributions must not:

- bypass CAPTCHA or Cloudflare protections;
- automate appointment booking;
- create artificial priority for users;
- overload external services;
- collect unnecessary personal data;
- expose secrets, cookies, tokens, or user sessions.

## Language

English is the primary language for source code and technical documentation.

Ukrainian and Russian translations of user-facing documentation are welcome.

## Questions

Open a GitHub Issue for proposals, technical questions, or documentation improvements.
