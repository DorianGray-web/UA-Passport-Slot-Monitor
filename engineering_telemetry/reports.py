"""Deterministic daily, weekly, and monthly engineering telemetry reports."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from .store import SQLiteEngineeringTelemetryStore

class AuditPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

def _bounds(period: AuditPeriod, anchor: datetime) -> tuple[datetime, datetime]:
    if anchor.tzinfo is None:
        raise ValueError("anchor must use UTC")
    anchor = anchor.astimezone(timezone.utc)
    if period is AuditPeriod.DAILY:
        start = anchor.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)
    if period is AuditPeriod.WEEKLY:
        start = (anchor - timedelta(days=anchor.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=7)
    start = anchor.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, (start.replace(day=28) + timedelta(days=4)).replace(day=1)

def _timestamp(value: datetime) -> str:
    return value.isoformat()

def _table(title: str, values: Counter[str]) -> list[str]:
    lines = [f"### {title}", "", "| Value | Sessions |", "|---|---:|"]
    lines.extend(f"| {key} | {values[key]} |" for key in sorted(values))
    return lines + [""]

def render_audit_report(store: SQLiteEngineeringTelemetryStore, period: AuditPeriod, anchor: datetime) -> str:
    start, end = _bounds(period, anchor)
    sessions = store.sessions_between(_timestamp(start), _timestamp(end))
    metrics = store.metrics_between(_timestamp(start), _timestamp(end))
    duration = sum(row["duration_seconds"] for row in sessions)
    inputs = sum(row["input_tokens"] or 0 for row in sessions)
    outputs = sum(row["output_tokens"] or 0 for row in sessions)
    cached = sum(row["cached_tokens"] or 0 for row in sessions)
    known_cost = [row["estimated_cost_usd"] for row in sessions if row["estimated_cost_usd"] is not None]
    cost = sum(known_cost)
    outcomes = Counter(row["outcome"] for row in sessions)
    lines = [
        "# AI Engineering Telemetry Audit", "", f"- Period: `{period.value}`",
        f"- Start (UTC): `{_timestamp(start)}`", f"- End (UTC): `{_timestamp(end)}`", "",
        "## Consumption", "", f"- Sessions: {len(sessions)}", f"- Recorded duration: {duration} seconds",
        f"- Input tokens: {inputs}", f"- Output tokens: {outputs}", f"- Cached tokens: {cached}",
        f"- Estimated cost (known records): USD {cost:.4f}", f"- Sessions without cost estimate: {len(sessions) - len(known_cost)}",
        f"- Infrastructure metrics recorded: {len(metrics)}", "", "## Efficiency", "",
        f"- Completion rate: {(outcomes['COMPLETED'] / len(sessions) * 100) if sessions else 0:.1f}%",
        f"- Tokens per recorded hour: {((inputs + outputs) / duration * 3600) if duration else 0:.1f}",
        f"- Estimated cost per session: USD {(cost / len(sessions)) if sessions else 0:.4f}", "",
    ]
    for title, values in (("Providers", Counter(row["provider"] for row in sessions)), ("Models", Counter(row["model"] for row in sessions)), ("Agents", Counter(row["agent"] for row in sessions)), ("Workflow stages", Counter(row["workflow_stage"] for row in sessions)), ("Outcomes", outcomes)):
        lines.extend(_table(title, values))
    opportunities: list[str] = []
    if not sessions:
        opportunities.append("No telemetry was recorded for this period; no consumption conclusion is available.")
    if len(known_cost) < len(sessions):
        opportunities.append("Record estimated costs for more sessions before using cost comparisons for decisions.")
    if outcomes["FAILED"]:
        opportunities.append("Review failed sessions by workflow stage before increasing automation or model usage.")
    if sessions and len(Counter(row["model"] for row in sessions)) < 2:
        opportunities.append("Only one model was recorded; no model-efficiency comparison is available yet.")
    if not opportunities:
        opportunities.append("No deterministic optimization signal was identified from the retained aggregate facts.")
    lines.extend(["## Optimization opportunities", "", *(f"- {item}" for item in opportunities), "", "## Scope", "", "This local report contains aggregate engineering facts only. It does not include prompts, completions, provider credentials, runtime observations, browser state, or personal data.", ""])
    return "\n".join(lines)

def write_audit_report(store: SQLiteEngineeringTelemetryStore, period: AuditPeriod, anchor: datetime, output_directory: str | Path) -> Path:
    start, _ = _bounds(period, anchor)
    path = Path(output_directory) / f"{start.date().isoformat()}-{period.value}-ai-engineering-telemetry.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_audit_report(store, period, anchor), encoding="utf-8")
    return path
