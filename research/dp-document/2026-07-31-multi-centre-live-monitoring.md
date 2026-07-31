# Multi-centre Live Monitoring — 2026-07-31

> **Historical; completed and superseded in part — 2026-07-31:** The registry
> and nine-centre sample described below were implemented. A later bounded
> 3h57m run used the confirmed Madrid, Barcelona, London, and Milan profiles;
> all 79 explicitly enabled browser fallbacks reached `TIMES`. The session plan
> is retained as historical research context, while validation of the remaining
> centres and cross-centre correlation analysis remain open.

## Stage goal

Prepare a configurable nine-centre research sample for the next passive
observation session. This stage extends provider coverage only. It does not add
notifications, booking, fingerprinting, or new discovery semantics.

## Evidence provenance

The findings motivating this sample were reported by the project owner from
the 2026-07-30 passive investigation. They are user-provided live-observation
evidence, not repository-derived evidence, fixtures, automated monitor output,
or independently repeated validation.

Reported findings:

- London and Madrid exposed the same high-level queue workflow;
- Toronto and Chisinau exposed confirmed `NO_SLOTS` landing pages;
- several centres appeared to implement the same DP Document protocol;
- an earlier Bratislava `POSSIBLE_SLOTS` observation remains a motivation for
  evidence-first classification and guarded discovery.

Additional owner-provided passive browser evidence on 2026-07-31 confirmed
London's public `form=days` request with `ServiceCenterId=47` and
`ServiceId=4`. This confirms the identifiers used by the bounded London
research profile; it does not authorize identity verification or booking.
The owner subsequently confirmed the corresponding Milan public request with
`ServiceCenterId=4` and `ServiceId=4`; Milan is therefore also configured with
explicit identifiers rather than inferred values.

“Same protocol” means only comparable high-level landing, date-discovery, and
time-discovery stages. It does not establish identical endpoints, field names,
CSRF handling, request parameters, response schemas, or availability
semantics.

## Research sample

The editable registry is
`providers/dp-document/providers.json`.

| City | Enabled | Priority | Observation group | Research role |
|---|---:|---|---|---|
| Bratislava | yes | high | active | Preserve and compare the prior `POSSIBLE_SLOTS` signal |
| Berlin | yes | normal | control | Existing comparison centre |
| Kortrijk | yes | normal | control | Existing historical baseline |
| Madrid | yes | high | active | Reported date/time workflow |
| London | yes | high | active | Reported date/time workflow |
| Milan | yes | high | active | Reported date/time workflow from the 2026-07-30 session |
| Toronto | yes | normal | control | Reported `NO_SLOTS` landing baseline |
| Chisinau | yes | normal | control | Reported `NO_SLOTS` landing baseline |
| Barcelona | yes | high | active | Confirmed public `DAYS`/`TIMES` positive control |

Priority is research scheduling metadata; it does not change process priority,
polling intervals, diagnostic queue priority, or classification behavior.
`observation_group` controls the analytical sample label. Changing `enabled`,
`priority`, or the group requires no protocol-code modification.

## Why use a control group?

Observing active and control centres over the same period helps distinguish a
local centre change from a platform-wide deployment or shared frontend
change. For example, simultaneous changes in Madrid, London, and Milan while
Toronto and Chisinau remain `NO_SLOTS` provide a stronger comparative signal
than isolated observations. They still do not prove a causal relationship.

## Observation-session plan

1. Review the registry immediately before the session and adjust only
   `enabled`, `priority`, and `research.observation_group` if the sample changes.
2. Start all enabled processes with `python -m monitor_runner`.
3. Record the shared `run_id` from `logs/orchestrator.log`.
4. Confirm that every process creates its city log and JSONL metadata stream.
5. Let the sample run over the same observation window.
6. Stop through `Ctrl+C` so the orchestrator records the session boundary.
7. Analyze immutable Observations by `run_id`, city, group, state, evidence,
   page hash, and time.

Expected JSONL streams:

```text
metadata/
    bratislava.jsonl
    berlin.jsonl
    kortrijk.jsonl
    madrid.jsonl
    london.jsonl
    milan.jsonl
    toronto.jsonl
    chisinau.jsonl
    barcelona.jsonl
```

Each Observation already records:

- landing state;
- HTTP status;
- discovery stage;
- typed evidence;
- HTML-change flag;
- page hash;
- request duration.

The authoritative records remain in `data/observations.sqlite3`; JSONL files
are analysis mirrors. No notification logic is part of this research stage.
