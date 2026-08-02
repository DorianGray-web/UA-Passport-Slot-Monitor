# Release Policy

## Scope

This policy defines the project-wide release acceptance process. It is
independent of provider implementations, transport mechanisms, runtime
architecture, individual research milestones, and specific project versions.
Every release of this repository must satisfy this policy.

## Release principle

> A release is ready only when runtime, documentation, governance, and
> evidence are mutually consistent and every enabled capability is fully
> traceable from observed evidence to runtime execution.

## Three independent release gates

One passing gate cannot compensate for another failing gate.

### Technical readiness

- all tests and compilation checks pass;
- `providers.json` validates and matches runtime entrypoints;
- internal links and anchors resolve;
- `git diff --check` passes;
- no runtime artifacts or secrets are tracked.

### Governance readiness

- the Evidence Matrix matches `providers.json`;
- every enabled capability has an explicit reviewed decision;
- evidence-confirmed but unapproved deployments remain disabled;
- candidate evidence has not promoted or demoted capabilities automatically;
- runtime refusal has not altered trusted configuration.

### Traceability readiness

Every enabled runtime capability must have a complete chain:

```text
Research Note
  -> Evidence Matrix
  -> Governance Review
  -> providers.json
  -> Runtime
```

## Release axioms

- Trust is declared, not inferred.
- Evidence accumulates.
- Interpretations evolve.
- Trusted capabilities are governed.
- Runtime validates every execution.
- Runtime fails closed whenever validation fails.

## Epistemic consistency

Epistemic consistency is the maintained agreement between observed facts,
retained evidence, documented interpretations, governed capabilities, trusted
configuration, and actual runtime behaviour.

Every adjacent layer must be explainable by the layer above it, and every
runtime capability must be traceable back to documented evidence and an
explicit governance decision.

## Release decision

A release is accepted only when Technical Readiness, Governance Readiness, and
Traceability Readiness all pass. Otherwise the release is **NOT READY**.

## Policy evolution

This policy may evolve through the same explicit governance discipline used
for trusted provider capabilities. Release criteria may become stricter over
time but should not become less traceable.
