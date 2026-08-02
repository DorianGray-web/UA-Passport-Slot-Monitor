# Research

This directory contains sanitized, reproducible conclusions from provider feasibility studies and user research.

Research artifacts are not production implementations. A documented observation may still require reliability testing, normalization, safety review, and adapter development.

## Current studies

- [DP Document queue workflow](dp-document/queue-workflow.md)
- [Valencia live observation](dp-document/2026-08-01-valencia-live-observation.md)
- [Berlin public discovery live observation](dp-document/2026-08-01-berlin-live-observation.md)
- [Toronto public discovery live observation](dp-document/2026-08-01-toronto-live-observation.md)
- [Cologne public discovery live observation](dp-document/2026-08-01-cologne-live-observation.md)
- [Bratislava public discovery live observation](dp-document/2026-08-01-bratislava-live-observation.md)
- [Prague public discovery live observation](dp-document/2026-08-02-prague-live-observation.md)
- [Kortrijk candidate form observation](dp-document/2026-08-02-kortrijk-candidate-form-observation.md)
- [Seven-centre 12-hour runtime validation](dp-document/2026-08-02-seven-centre-12h-runtime-validation.md)
- [Seven-centre six-hour release validation](dp-document/2026-08-02-seven-centre-6h-release-validation.md)
- [Cross-deployment public discovery comparison](dp-document/2026-08-01-cross-deployment-public-discovery-comparison.md)
- [Seven-centre candidate evidence plan](dp-document/2026-08-01-seven-centre-candidate-evidence-plan.md)

## Run summaries

Long orchestrated runs produce local Markdown summaries in `dp-document/`.
These generated reports are runtime output and are ignored by Git. The
generator reads only the immutable Observation payloads;
it does not read browser profiles, raw HTML, cookies, headers, or captures.
Each report is scoped to one `run_id` and separates observed facts from
interpretation.
Only manually reviewed, sanitized conclusions should be promoted into
committed research notes.

Manual generation:

```powershell
.\.venv-2\Scripts\python.exe .\research\dp-document\tools\generate_research_summary.py --run-id RUN-...
```

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
