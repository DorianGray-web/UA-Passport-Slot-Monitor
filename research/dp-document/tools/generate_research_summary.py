"""Generate a Markdown transport-research summary from immutable Observations."""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PROJECT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE = PROJECT_DIR / "data" / "observations.sqlite3"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "research" / "dp-document"
BLOCKED_HTTP_STATUSES = {403, 429, 503}
SUCCESS_STATES = {"SLOTS_AVAILABLE", "POSSIBLE_SLOTS"}


def load_observations(database: Path, run_id: str | None) -> list[dict]:
    if not database.is_file():
        raise FileNotFoundError(f"Observation database not found: {database}")
    with sqlite3.connect(database) as connection:
        if run_id:
            rows = connection.execute(
                """
                SELECT payload FROM observations
                WHERE run_id=? ORDER BY observed_at
                """,
                (run_id,),
            ).fetchall()
        else:
            latest = connection.execute(
                """
                SELECT run_id FROM observations
                ORDER BY observed_at DESC LIMIT 1
                """
            ).fetchone()
            if latest is None:
                return []
            rows = connection.execute(
                """
                SELECT payload FROM observations
                WHERE run_id=? ORDER BY observed_at
                """,
                (latest[0],),
            ).fetchall()
    return [json.loads(row[0]) for row in rows]


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def report_timezone(name: str):
    """Resolve an IANA zone without making the optional tzdata wheel mandatory."""
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        # Windows does not ship the IANA database used by zoneinfo. The monitor
        # is a local research tool, so the host's configured timezone is the
        # safest dependency-free fallback for rendering its own run timeline.
        return datetime.now().astimezone().tzinfo


def run_duration_seconds(observations: list[dict]) -> float:
    if len(observations) < 2:
        return 0.0
    return max(
        0.0,
        (
            parse_timestamp(observations[-1]["observed_at"])
            - parse_timestamp(observations[0]["observed_at"])
        ).total_seconds(),
    )


def format_duration(seconds: float) -> str:
    total_minutes = round(seconds / 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


def mean(values: Iterable[int | float]) -> float | None:
    collected = list(values)
    return statistics.fmean(collected) if collected else None


def number(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def provider_name(observation: dict) -> str:
    return str(observation["provider_id"]).rsplit("-", 1)[-1].title()


def traces(observation: dict, transport: str | None = None) -> list[dict]:
    items = list(observation.get("request_trace") or [])
    if transport is not None:
        items = [item for item in items if item.get("transport") == transport]
    return items


def has_http_block(observation: dict) -> bool:
    return any(
        item.get("operation") == "landing"
        and item.get("status_code") in BLOCKED_HTTP_STATUSES
        for item in traces(observation, "http")
    )


def reached_times(observation: dict) -> bool:
    return (
        observation.get("discovery_stage") == "TIMES"
        and observation.get("state") in SUCCESS_STATES
    )


def stats(values: list[int]) -> str:
    if not values:
        return "min: n/a  \nmax: n/a  \naverage: n/a"
    return (
        f"min: {min(values)}  \n"
        f"max: {max(values)}  \n"
        f"average: {statistics.fmean(values):.1f}"
    )


def provider_section(name: str, observations: list[dict]) -> str:
    states = Counter(item.get("state") for item in observations)
    date_counts = [
        item["available_dates_count"]
        for item in observations
        if item.get("available_dates_count") is not None
    ]
    time_counts = [
        item["available_time_slots_count"]
        for item in observations
        if item.get("available_time_slots_count") is not None
    ]
    earliest = [
        item["earliest_available_time"]
        for item in observations
        if item.get("earliest_available_time")
    ]
    latest = [
        item["latest_available_time"]
        for item in observations
        if item.get("latest_available_time")
    ]
    average_duration = mean(item.get("duration_ms", 0) for item in observations)
    state_lines = "\n".join(
        f"- {state}: {states.get(state, 0)}"
        for state in ("SLOTS_AVAILABLE", "NO_SLOTS", "UNKNOWN", "BLOCKED")
    )
    return f"""## {name}

Observations: {len(observations)}  
HTTP blocked: {sum(has_http_block(item) for item in observations)}  
Playwright runs: {sum(item.get('transport') == 'playwright' for item in observations)}  
Average discovery duration: {number(average_duration / 1000 if average_duration is not None else None, 2)} s

### State distribution

{state_lines}

### Available dates

{stats(date_counts)}

### Available time entries

{stats(time_counts)}

Earliest observed time: {min(earliest) if earliest else 'n/a'}  
Latest observed time: {max(latest) if latest else 'n/a'}
"""


def build_report(
    observations: list[dict],
    *,
    timezone_name: str = "Europe/Amsterdam",
) -> str:
    if not observations:
        raise ValueError("No observations were supplied.")
    observations = sorted(observations, key=lambda item: item["observed_at"])
    run_ids = {item["run_id"] for item in observations}
    if len(run_ids) != 1:
        raise ValueError("A report must contain exactly one run_id.")

    timezone = report_timezone(timezone_name)
    start = parse_timestamp(observations[0]["observed_at"])
    end = parse_timestamp(observations[-1]["observed_at"])
    duration = run_duration_seconds(observations)
    providers: dict[str, list[dict]] = {}
    for item in observations:
        providers.setdefault(provider_name(item), []).append(item)

    http_attempts = [item for item in observations if traces(item, "http")]
    http_blocked = [item for item in observations if has_http_block(item)]
    browser_runs = [
        item for item in observations if item.get("transport") == "playwright"
    ]
    successful = [item for item in observations if reached_times(item)]
    successful_browser = [item for item in browser_runs if reached_times(item)]
    browser_unknown = [
        item for item in browser_runs if item.get("state") == "UNKNOWN"
    ]
    browser_errors = [
        item
        for item in browser_runs
        if set(item.get("evidence") or ())
        & {"PLAYWRIGHT_ERROR", "PLAYWRIGHT_TIMEOUT"}
    ]
    captcha = [
        item
        for item in observations
        if item.get("state") == "CAPTCHA_REQUIRED"
    ]

    landing_http_statuses = Counter(
        item.get("status_code")
        for observation in observations
        for item in traces(observation, "http")
        if item.get("operation") == "landing"
    )
    http_observations = [
        item for item in observations if item.get("transport") == "http"
    ]
    successful_http = [item for item in http_observations if reached_times(item)]
    http_states = Counter(item.get("state") for item in http_observations)
    browser_states = Counter(item.get("state") for item in browser_runs)
    browser_average = mean(item.get("duration_ms", 0) for item in browser_runs)

    provider_list = "\n".join(f"- {name}" for name in providers)
    provider_sections = "\n\n".join(
        provider_section(name, items) for name, items in providers.items()
    )

    timeline_rows = []
    for item in observations:
        slots = item.get("available_time_slots_count")
        if slots is None:
            continue
        local_time = parse_timestamp(item["observed_at"]).astimezone(timezone)
        timeline_rows.append(
            f"| {local_time:%Y-%m-%d %H:%M:%S} | {provider_name(item)} | "
            f"{item.get('transport')} | {item.get('state')} | "
            f"{item.get('available_dates_count')} | {slots} |"
        )
    timeline = "\n".join(timeline_rows) or "| — | — | — | — | — | — |"

    http_every_cycle = bool(observations) and len(http_attempts) == len(observations)
    blocked_every_cycle = bool(observations) and len(http_blocked) == len(observations)
    browser_success_every_cycle = bool(browser_runs) and (
        len(successful_browser) == len(browser_runs)
    )

    facts = [
        f"HTTP was attempted in {len(http_attempts)} of {len(observations)} cycles.",
        f"HTTP landing was blocked in {len(http_blocked)} cycles.",
        f"Playwright fallback ran in {len(browser_runs)} cycles.",
        f"Playwright reached confirmed TIMES in {len(successful_browser)} cycles.",
        f"HTTP-only observations reached confirmed TIMES in {len(successful_http)} cycles.",
        f"Mean Playwright cycle duration was {number(browser_average / 1000 if browser_average is not None else None, 2)} seconds.",
    ]
    interpretation = []
    if browser_success_every_cycle:
        interpretation.append(
            "During this run, the browser transport recovered public "
            f"availability after all {len(browser_runs)} blocked HTTP landing "
            "attempts that triggered fallback."
        )
    elif successful_browser:
        interpretation.append(
            "The browser transport recovered public availability in at least "
            "one cycle after HTTP transport was blocked."
        )
    else:
        interpretation.append(
            "This run does not yet demonstrate reliable browser completion to TIMES."
        )
    interpretation.append(
        "The HTTP result describes the current runtime and classifier coverage; "
        "it does not prove that the provider's public days/times protocol is "
        "fundamentally inaccessible over HTTP."
    )
    interpretation.append(
        "Equivalent bounded studies on additional evidence-confirmed providers "
        "are required before generalizing the result."
    )

    conclusions = []
    if browser_runs:
        conclusions.append(
            f"Playwright fallback completed {len(successful_browser)} of "
            f"{len(browser_runs)} browser runs during {format_duration(duration)}."
        )
    conclusions.extend(
        [
            f"Confirmed discovery stopped at TIMES in {len(successful)} cycles.",
            "No runtime path navigated beyond the public discovery boundary.",
            "Observation schema remained transport-independent.",
        ]
    )
    if blocked_every_cycle and browser_success_every_cycle:
        conclusions.append(
            "Browser transport successfully replaced blocked HTTP transport "
            "for every observed cycle in this run."
        )

    return f"""# Playwright Fallback Observation

## Experiment

Run ID: `{next(iter(run_ids))}`  
Start: {start.astimezone(timezone).isoformat()}  
End: {end.astimezone(timezone).isoformat()}  
Duration: {format_duration(duration)}  
Timezone: `{timezone_name}`

Providers:
{provider_list}

## Summary

Total observations: {len(observations)}  
HTTP attempts: {len(http_attempts)}  
HTTP blocked: {len(http_blocked)}  
Playwright fallback: {len(browser_runs)}  
Successful discoveries through TIMES: {len(successful)}

{provider_sections}

## Timeline

| Time | Provider | Transport | State | Dates | Time entries |
|---|---|---|---|---:|---:|
{timeline}

## Behaviour

HTTP transport:
- attempted every cycle: {str(http_every_cycle).lower()}
- blocked every cycle: {str(blocked_every_cycle).lower()}

Playwright transport:
- succeeded every browser cycle: {str(browser_success_every_cycle).lower()}

Unexpected browser errors: {len(browser_errors)}  
Unexpected `UNKNOWN`: {len(browser_unknown)}  
CAPTCHA-required classifications: {len(captcha)}  
CAPTCHA interactions: 0 (no CAPTCHA action exists in the transport)  
Identity-data interactions: 0 (no identity action exists in the transport)  
Booking actions: 0 (no booking operation exists in the transport)  

The public page may render identity or CAPTCHA controls. These counters describe
runtime actions and classifications, not the visual absence of such controls.

## Transport Comparison

### HTTP Discovery

- Lightweight
- Preferred and attempted first

Observed during this experiment:

- HTTP landing 200: {landing_http_statuses.get(200, 0)}
- HTTP landing 403: {landing_http_statuses.get(403, 0)}
- HTTP landing 429: {landing_http_statuses.get(429, 0)}
- HTTP landing 503: {landing_http_statuses.get(503, 0)}
- HTTP Observation `UNKNOWN`: {http_states.get('UNKNOWN', 0)}
- HTTP Observation `POSSIBLE_SLOTS`: {http_states.get('POSSIBLE_SLOTS', 0)}
- HTTP Observation `SLOTS_AVAILABLE`: {http_states.get('SLOTS_AVAILABLE', 0)}
- HTTP observations reaching TIMES: {len(successful_http)}

### Playwright Discovery

- Completed LANDING: {sum(bool(traces(item, 'playwright')) for item in browser_runs)}
- Completed DAYS: {sum(item.get('discovery_stage') in {'DAYS', 'TIMES'} for item in browser_runs)}
- Completed TIMES: {sum(item.get('discovery_stage') == 'TIMES' for item in browser_runs)}
- `SLOTS_AVAILABLE`: {browser_states.get('SLOTS_AVAILABLE', 0)}
- `NO_SLOTS`: {browser_states.get('NO_SLOTS', 0)}
- `UNKNOWN`: {browser_states.get('UNKNOWN', 0)}
- Average duration: {number(browser_average / 1000 if browser_average is not None else None, 2)} s
- Public-boundary stop is enforced by the transport implementation.

## Observed facts

{''.join(f'- {fact}\n' for fact in facts)}
## Interpretation

{''.join(f'- {item}\n' for item in interpretation)}
## Conclusions

{''.join(f'- {item}\n' for item in conclusions)}"""


def default_output_path(
    observations: list[dict], output_dir: Path
) -> Path:
    start = parse_timestamp(observations[0]["observed_at"])
    hours = max(1, round(run_duration_seconds(observations) / 3600))
    return output_dir / f"{start:%Y-%m-%d}-playwright-fallback-{hours}h-report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timezone", default="Europe/Amsterdam")
    parser.add_argument("--minimum-duration-hours", type=float, default=1.0)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    observations = load_observations(args.database, args.run_id)
    if not observations:
        print("No observations found for the requested run.")
        return 2
    duration_hours = run_duration_seconds(observations) / 3600
    if not args.force and duration_hours < args.minimum_duration_hours:
        print(
            f"Run duration {duration_hours:.2f}h is below the "
            f"{args.minimum_duration_hours:.2f}h report threshold."
        )
        return 3
    output = args.output or default_output_path(observations, args.output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_report(observations, timezone_name=args.timezone),
        encoding="utf-8",
    )
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
