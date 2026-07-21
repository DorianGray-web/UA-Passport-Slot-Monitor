# Research

This directory contains sanitized, reproducible conclusions from provider feasibility studies and user research.

Research artifacts are not production implementations. A documented observation may still require reliability testing, normalization, safety review, and adapter development.

## Current studies

- [DP Document queue workflow](dp-document/queue-workflow.md)
- [Notification-channel survey](user-surveys/notification-channels.md)

## Evidence levels

Research notes should distinguish between:

- **Confirmed** — directly observed in the public application or collected research data;
- **In progress** — currently being tested and not yet reliable enough for implementation;
- **Hypothesis** — plausible but not yet verified;
- **Implemented** — available in project code and covered by appropriate tests.

## Repository safety

Only sanitized conclusions belong in the public repository. Do not commit:

- browser profiles, cookies, tokens, or fingerprints;
- CAPTCHA data;
- raw HTML or network captures;
- personal data from users or survey respondents;
- detailed payloads or step-by-step internal request recipes;
- secrets, authorization headers, or API keys.
