# Web form implementation boundaries

## Scope

These instructions apply to implementation work inside
research/user-surveys/survey/web-form/. They supplement the repository and
user-research AGENTS.md files.

## Writable scope

For a web-form implementation task, agents may create and modify files only
inside research/user-surveys/survey/web-form/.

## Required read-only context

Before implementation, read:

- ../spec/
- ../../shared/taxonomy/
- ../../shared/schemas/
- ../../AGENTS.md

These paths are context only. Do not modify them as part of a web-form task.
If they are not available in the current workspace, stop and request that the
required context be added rather than inventing questions, IDs, or contracts.

## Forbidden changes

Do not modify:

- ../spec/
- ../results/
- ../google-apps-script/
- ../../shared/
- ../../social-listening/
- ../../synthesis/
- files outside research/user-surveys/survey/web-form/

Do not add personal data, secrets, API keys, deployment URLs, raw exports, raw
comments, contact collection, fingerprinting, or hidden identifiers.

## Implementation contract

- Implement the approved survey specification without changing product
  decisions.
- Generate centre, problem, and notification options from their canonical
  taxonomy owners where specified.
- Use stable ASCII IDs in payloads and localized labels only for display.
- Do not add, remove, rename, regroup, or reclassify centres.
- Do not change question IDs, enums, requiredness, branching, analytical
  semantics, transport, retry, or idempotency rules.
- Preserve answers and validation state when the locale changes.
- Treat all free text as untrusted plain text.
- Report a specification, taxonomy, schema, or Apps Script conflict instead of
  resolving it silently.
