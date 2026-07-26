# AI Workflow

This directory defines the project-local agent workflow.

## Artifact chain

research evidence -> specification -> implementation plan -> code -> verification report -> reusable insight

## Rules

- Agents exchange durable repository artifacts, not undocumented chat context.
- Research findings must distinguish confirmed evidence from hypotheses.
- Specifications define WHAT and WHY; plans define HOW.
- Implementation must trace changes to acceptance-criteria IDs.
- Verification is read-only except for reports.
- Runtime browser profiles, captures, logs, tokens, and personal data never enter Git.
