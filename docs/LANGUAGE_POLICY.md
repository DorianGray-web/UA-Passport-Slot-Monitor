# Language Policy

> **Status: Draft**
>
> This document describes the current language policy of UA Passport Slot Monitor.
> The project is still in the design and validation stage, so this policy may be
> refined as the contributor base, translation tooling, and user-facing surfaces
> (web app, notifications, documentation) are implemented.

## 1. Why this document exists

UA Passport Slot Monitor targets Ukrainians living abroad, while aiming to stay
open to an international pool of contributors, reviewers, and security
researchers. This creates two audiences with different language needs:

- **Contributors and maintainers**, who need one predictable language for code
  and technical collaboration;
- **End users**, many of whom are more comfortable in Ukrainian or Russian than
  in English.

This policy defines which language applies where, so that both audiences are
served without fragmenting the project's technical documentation.

## 2. Primary language: English

English is the single primary language for:

- source code (identifiers, variables, function and class names);
- code comments;
- commit messages and pull request titles/descriptions;
- issue reports and technical discussion;
- architecture, security, and privacy documentation (`ARCHITECTURE.md`,
  `SECURITY.md`, `PRIVACY.md`, `PROJECT_CONCEPT.md`, `ROADMAP.md`, etc.);
- API and configuration naming.

Keeping technical documentation and code in one language avoids duplicated,
diverging copies of documents that define security or privacy guarantees, and
keeps the project reviewable by international contributors and security
researchers.

## 3. User-facing content: Ukrainian, Russian, and English

Because the target users are primarily Ukrainians abroad, user-facing surfaces
should be usable without English:

- the web application interface;
- notification messages (Telegram, email, and future channels);
- onboarding and help content;
- the `README.md` (a Ukrainian and/or Russian translation is welcome
  alongside the English original, e.g. `docs/uk/README.md`, `docs/ru/README.md`).

Ukrainian and Russian translations of user-facing documentation are welcome
contributions, as already stated in `CONTRIBUTING.md`. Additional languages
may be added later based on user demand identified through the project's
feedback channels (see the project survey linked from `README.md`).

## 4. Translations are secondary, not authoritative

For any document that exists in more than one language:

- the **English version is the source of truth**;
- translated versions must clearly indicate which English revision (commit or
  date) they correspond to;
- a translation that has fallen behind the English source should be marked as
  outdated rather than silently left inconsistent, until it is updated.

This applies to both documentation and, once implemented, user-facing
application strings (e.g. via a standard i18n/localization file structure).

## 5. Issues, discussions, and pull requests

- Technical discussion, code review, and architecture proposals should be in
  English so that all maintainers and contributors can participate.
- Bug reports describing a real-world usage problem (e.g. behaviour of a
  specific document center's website) may be submitted in Ukrainian or
  Russian if the reporter is not comfortable in English; a short English
  summary is appreciated but not required.
- Maintainers may translate or summarize non-English issues for broader
  visibility.

## 6. Localization implementation (future)

Once the application reaches implementation stage, this policy expects:

- a standard localization/i18n mechanism for interface strings, rather than
  hardcoded text in a single language;
- English as the default/fallback locale;
- Ukrainian and Russian as the initial supported locales for the interface
  and notifications;
- no personal or sensitive data embedded in translation files.

This section will be expanded with concrete tooling and file structure once
localization is implemented.

## 7. Changes to this policy

This policy may be updated as the contributor base grows or as new
user-facing surfaces are introduced. Material changes should be documented in
the repository history and, where relevant, in `CHANGELOG.md`.

**Last updated:** 2026-07-20
