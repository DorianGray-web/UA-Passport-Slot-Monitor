from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPT = (
    PROJECT_DIR
    / "research"
    / "dp-document"
    / "tools"
    / "generate_research_summary.py"
)
SPEC = importlib.util.spec_from_file_location("research_summary", SCRIPT)
assert SPEC and SPEC.loader
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)


def observation(
    *,
    provider: str,
    observed_at: str,
    transport: str,
    state: str,
    stage: str,
    duration_ms: int,
    dates: int | None = None,
    slots: int | None = None,
    earliest: str | None = None,
    latest: str | None = None,
    http_status: int = 403,
    evidence: list[str] | None = None,
) -> dict:
    trace = [
        {
            "method": "GET",
            "operation": "landing",
            "status_code": http_status,
            "duration_ms": 50,
            "response_bytes": 500,
            "attempt": 1,
            "transport": "http",
        }
    ]
    if transport == "playwright":
        trace.extend(
            [
                {
                    "method": "GET",
                    "operation": "landing",
                    "status_code": 200,
                    "duration_ms": 500,
                    "response_bytes": 5000,
                    "attempt": 1,
                    "transport": "playwright",
                },
                {
                    "method": "POST",
                    "operation": "days",
                    "status_code": 200,
                    "duration_ms": 100,
                    "response_bytes": 200,
                    "attempt": 1,
                    "transport": "playwright",
                },
                {
                    "method": "POST",
                    "operation": "times",
                    "status_code": 200,
                    "duration_ms": 100,
                    "response_bytes": 300,
                    "attempt": 1,
                    "transport": "playwright",
                },
            ]
        )
    return {
        "run_id": "RUN-test",
        "provider_id": f"dp-document-{provider}",
        "observed_at": observed_at,
        "transport": transport,
        "state": state,
        "duration_ms": duration_ms,
        "http_status": 200 if transport == "playwright" else http_status,
        "discovery_stage": stage,
        "evidence": evidence
        if evidence is not None
        else ["AVAILABLE_DATES_FOUND", "AVAILABLE_TIMES_FOUND"],
        "request_trace": trace,
        "available_dates_count": dates,
        "available_time_slots_count": slots,
        "earliest_available_time": earliest,
        "latest_available_time": latest,
    }


class ResearchSummaryTests(unittest.TestCase):
    def test_report_aggregates_mixed_transport_observations(self) -> None:
        records = [
            observation(
                provider="madrid",
                observed_at="2026-07-31T11:00:00+00:00",
                transport="playwright",
                state="SLOTS_AVAILABLE",
                stage="TIMES",
                duration_ms=10_000,
                dates=10,
                slots=231,
                earliest="10:00:00",
                latest="18:30:00",
            ),
            observation(
                provider="barcelona",
                observed_at="2026-07-31T15:00:00+00:00",
                transport="playwright",
                state="SLOTS_AVAILABLE",
                stage="TIMES",
                duration_ms=12_000,
                dates=12,
                slots=325,
                earliest="09:45:00",
                latest="19:00:00",
            ),
        ]

        report = SUMMARY.build_report(records)

        self.assertIn("Run ID: `RUN-test`", report)
        self.assertIn("Duration: 4h 0m", report)
        self.assertIn("Observation coverage duration: 4h 0m", report)
        self.assertIn("HTTP blocked: 2", report)
        self.assertIn("Playwright runs: 2", report)
        self.assertIn("## Madrid", report)
        self.assertIn("## Barcelona", report)
        self.assertIn("| 2026-07-31 13:00:00 | Madrid", report)
        self.assertIn("HTTP landing 403: 2", report)
        self.assertIn("`SLOTS_AVAILABLE`: 2", report)
        self.assertIn("Unexpected browser errors: 0", report)
        self.assertIn("CAPTCHA interactions: 0", report)
        self.assertIn("Identity-data interactions: 0", report)
        self.assertIn("Booking actions: 0", report)
        self.assertIn("current runtime and classifier coverage", report)
        self.assertIn("## Observed facts", report)
        self.assertIn("## Interpretation", report)
        self.assertIn("## Conclusions", report)

    def test_candidate_landing_probe_is_separate_from_discovery_results(self) -> None:
        records = [
            observation(
                provider="berlin",
                observed_at="2026-08-01T10:00:00+00:00",
                transport="playwright",
                state="UNKNOWN",
                stage="LANDING",
                duration_ms=2_000,
                evidence=[
                    "CANDIDATE_EVIDENCE_PROBE",
                    "QUEUE_FORM_FOUND",
                    "SERVICE_SELECTOR_FOUND",
                    "SERVICE_OPTIONS_FOUND",
                ],
            )
        ]

        report = SUMMARY.build_report(records)

        self.assertIn("Candidate landing probes: 1", report)
        self.assertIn("## Candidate Landing Probes", report)
        self.assertIn("Runs: 1", report)
        self.assertIn("Queue form detected: 1", report)
        self.assertIn("Service selector detected: 1", report)
        self.assertIn("Service options detected: 1", report)
        self.assertIn("Unexpected `UNKNOWN`: 0", report)
        self.assertIn("Successful discoveries through TIMES: 0", report)

    def test_confirmed_early_no_slots_is_a_bounded_browser_outcome(self) -> None:
        records = [
            observation(
                provider="berlin",
                observed_at="2026-08-02T01:00:00+00:00",
                transport="playwright",
                state="NO_SLOTS",
                stage="LANDING",
                duration_ms=2_000,
            )
        ]

        report = SUMMARY.build_report(records)

        self.assertIn(
            "produced a recognized bounded outcome in every confirmed "
            "discovery run: true",
            report,
        )
        self.assertIn("stopped earlier at confirmed NO_SLOTS: 1", report)
        self.assertIn("recognized bounded outcomes in 1 of 1", report)

    def test_report_rejects_mixed_run_ids(self) -> None:
        records = [
            observation(
                provider="madrid",
                observed_at="2026-07-31T11:00:00+00:00",
                transport="http",
                state="BLOCKED",
                stage="LANDING",
                duration_ms=100,
            ),
            observation(
                provider="madrid",
                observed_at="2026-07-31T12:00:00+00:00",
                transport="http",
                state="BLOCKED",
                stage="LANDING",
                duration_ms=100,
            ),
        ]
        records[1]["run_id"] = "RUN-other"

        with self.assertRaisesRegex(ValueError, "exactly one run_id"):
            SUMMARY.build_report(records)

    def test_default_filename_uses_run_date_and_duration(self) -> None:
        records = [
            observation(
                provider="madrid",
                observed_at="2026-07-31T11:00:00+00:00",
                transport="http",
                state="BLOCKED",
                stage="LANDING",
                duration_ms=100,
            ),
            observation(
                provider="madrid",
                observed_at="2026-07-31T15:00:00+00:00",
                transport="http",
                state="BLOCKED",
                stage="LANDING",
                duration_ms=100,
            ),
        ]
        path = SUMMARY.default_output_path(records, Path("research"))
        self.assertEqual(
            path.name,
            "2026-07-31-playwright-fallback-4h-report.md",
        )

    def test_runtime_duration_is_distinct_from_observation_coverage(self) -> None:
        records = [
            observation(
                provider="madrid",
                observed_at="2026-08-01T11:02:38+00:00",
                transport="http",
                state="BLOCKED",
                stage="LANDING",
                duration_ms=100,
            ),
            observation(
                provider="madrid",
                observed_at="2026-08-01T23:01:40+00:00",
                transport="http",
                state="BLOCKED",
                stage="LANDING",
                duration_ms=100,
            ),
        ]

        report = SUMMARY.build_report(
            records,
            run_started_at=SUMMARY.parse_timestamp(
                "2026-08-01T11:02:29+00:00"
            ),
            run_ended_at=SUMMARY.parse_timestamp(
                "2026-08-01T23:05:38+00:00"
            ),
        )

        self.assertIn("Duration: 12h 3m", report)
        self.assertIn("Observation coverage duration: 11h 59m", report)


if __name__ == "__main__":
    unittest.main()
