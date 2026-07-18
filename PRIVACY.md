# Privacy Principles and Draft Policy

> **Status: Draft**
>
> This document describes the current privacy principles of UA Passport Slot Monitor.
> The project is still in the design and validation stage, so this policy may change as the architecture, supported services, notification methods, and data flows are implemented.
>
> The project is being designed with the principles of the EU General Data Protection Regulation (GDPR) in mind. This draft is not yet a claim of formal GDPR compliance. Compliance must be reviewed against the actual production implementation, infrastructure, third-party services, and operational procedures before a public release.

## 1. Privacy-first commitment

UA Passport Slot Monitor is designed according to the principles of privacy by design and by default, transparency, purpose limitation, data minimisation, storage limitation, integrity, confidentiality, and user control.

When privacy and convenience conflict, the project should prefer the option that collects less personal data and leaves more control with the user.

Before introducing any feature that requires personal data, the project should first ask:

> Can this feature work without collecting personal data?

If the answer is yes, the data should not be collected.

## 2. Data the project does not collect

UA Passport Slot Monitor is not intended to collect, request, or store:

- passport numbers;
- national identity card numbers;
- passport or ID scans;
- photographs of identity documents;
- biometric or facial recognition data;
- fingerprints;
- payment card or bank account information;
- credentials for government or official document-service websites;
- passwords entered on official websites;
- CAPTCHA answers or solved CAPTCHA images;
- copies of completed application forms;
- document application numbers;
- personal information entered during the final booking process;
- medical, political, religious, or other special-category personal data;
- contact lists from the user's device;
- browsing history unrelated to the project;
- data for advertising profiling;
- data intended for sale or commercial resale.

The project must not intentionally intercept information entered by the user on an official booking website.

## 3. Data the project may process

Depending on the final implementation and features selected by the user, the project may process a limited set of information such as:

- selected country;
- selected service centre;
- selected document service;
- preferred notification channel;
- notification destination, such as an email address or Telegram identifier;
- application settings;
- monitoring preferences;
- temporary session information required to maintain a user-controlled browser session;
- approximate or precise location, only when the user explicitly requests location-based centre suggestions.

Only information necessary for a clearly defined function should be processed.

The exact categories of processed data will be updated in this document before the corresponding feature is released.

## 4. Location data

Location access must be optional.

The user should be able to deny location permission, select a country and service centre manually, and revoke browser or device permission at any time.

Where technically possible:

- centre matching should be performed locally;
- exact coordinates should not be stored;
- location information should not be retained after the requested function is completed;
- location data should not be used for advertising, behavioural profiling, or unrelated analytics.

## 5. Browser sessions and CAPTCHA

The project may support persistent browser sessions to reduce repeated setup steps. Such sessions must remain under the user's control.

UA Passport Slot Monitor does not:

- automatically solve CAPTCHA;
- bypass CAPTCHA or Cloudflare;
- confirm appointments automatically;
- submit final registration without the user;
- collect information entered during final registration.

The user must personally review availability, complete CAPTCHA, select an appointment, and confirm the booking on the official website.

## 6. Purpose limitation and data minimisation

Any personal data processed by the project must have a specific and documented purpose.

The project should collect the smallest amount of information reasonably necessary for each feature. Anonymous or local processing should be preferred whenever possible.

A new feature should not be accepted merely because collecting additional data would make implementation easier.

## 7. Data storage and retention

Personal data must not be stored longer than necessary for its stated purpose.

Before production release, the project must define:

- where each category of data is stored;
- whether it is stored locally or remotely;
- the retention period;
- the deletion procedure;
- who can access it;
- how backups are handled.

Temporary data should be deleted automatically when it is no longer needed. Where local-only storage is sufficient, server-side storage should be avoided.

## 8. Third-party services

The project may rely on external services for notifications, hosting, error reporting, or infrastructure.

Before a third-party service is introduced, the project should evaluate what data it receives, where the data is processed, whether international transfers are involved, whether the service is necessary, and whether a more privacy-preserving alternative exists.

Third-party services must be documented in this policy before they are used in a public production version.

The project will not sell personal data or share it with data brokers or advertising networks.

## 9. Analytics and telemetry

Privacy-invasive analytics should not be enabled by default.

If analytics or diagnostic telemetry is introduced:

- its purpose must be documented;
- the collected fields must be listed;
- sensitive information must be excluded;
- collection should be optional where reasonably possible;
- users should be informed before collection begins;
- retention must be limited;
- IP addresses and identifiers should be minimised or anonymised where possible.

## 10. Security and logging

Reasonable technical and organisational measures should be applied according to the risks of the implemented system.

These may include encryption in transit, encryption at rest where appropriate, restricted access, secure secret management, dependency review, secure logging, vulnerability reporting, and regular review of data flows.

Sensitive values, API keys, tokens, and user information must not be committed to the public repository.

Application logs must not intentionally contain passport information, passwords, authentication tokens, CAPTCHA answers, complete notification credentials, or personal information entered on official websites.

Security issues should be reported according to [SECURITY.md](SECURITY.md).

## 11. User rights and control

Before the project processes personal data in production, users should receive clear information about:

- what data is processed;
- why it is processed;
- where it is stored;
- how long it is retained;
- how to access, correct, export, or delete it;
- how to withdraw consent where processing relies on consent;
- how to contact the project regarding privacy.

The implementation should make deletion and permission withdrawal practical, not merely theoretical.

## 12. Children and vulnerable users

The project is not intended to independently collect children's personal data.

A parent or legal guardian may monitor appointment availability for a child, but the project should still avoid collecting the child's passport, identity, biometric, or application data.

Any future feature specifically involving children requires a separate privacy and legal review before implementation.

## 13. Contributors and access to user data

Contributions from Europe, Ukraine, and other countries are welcome.

All contributors, maintainers, reviewers, service providers, and future collaborators must follow the same privacy, security, and ethical principles regardless of their location.

Participation in the open-source project does not grant access to user data.

Access to production systems or personal data, if such systems later exist, must be necessary for a defined role, limited to the minimum required level, documented, revocable, and protected by appropriate security measures.

**Open-source code does not mean open user data.**

## 14. Independent project status

UA Passport Slot Monitor is currently an independent open-source initiative and is not officially affiliated with DP “Document”, Ukrainian government institutions, or other official service providers.

The project is open to constructive dialogue and possible future cooperation with official service providers, provided that such cooperation respects applicable law, user privacy, information security, transparency, voluntary user choice, and the principle that final booking decisions remain with the user.

## 15. Changes to this policy

This policy is expected to evolve as the project develops.

Changes may be required when:

- a new feature is introduced;
- the technical architecture changes;
- a backend or database is added;
- a new notification provider is integrated;
- analytics or error reporting is introduced;
- legal or regulatory requirements change;
- an official cooperation model is established.

Material changes should be documented in the repository history and, where relevant, in `CHANGELOG.md`.

The current version of this document should always reflect the data flows of the latest public release.

## 16. Contact and privacy questions

A dedicated privacy contact method will be added before the project processes personal data in a public production environment.

Until then, privacy-related questions and proposals may be submitted through the repository's GitHub Issues or Discussions. Users should never publish personal documents, passport information, credentials, or other sensitive data in a public issue.

---

## Current implementation notice

At the time of this draft, UA Passport Slot Monitor is in the design and validation stage.

This document defines the intended privacy boundaries of the project. It does not claim that every described feature has already been implemented.

**Last updated:** 2026-07-19
