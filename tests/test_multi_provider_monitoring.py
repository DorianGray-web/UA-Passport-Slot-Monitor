from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROVIDER_DIR = PROJECT_DIR / "providers" / "dp-document"
sys.path.insert(0, str(PROVIDER_DIR))

from city_monitor import CityMonitor, ProviderConfig, QueueState  # noqa: E402
from diagnostics.domain import RequestTraceEntry  # noqa: E402
from provider_registry import load_provider_registry  # noqa: E402
from monitor_runner import (  # noqa: E402
    configured_providers,
    configured_run_duration_seconds,
    generate_research_summary,
)


class MultiProviderMonitoringTests(unittest.TestCase):
    def make_monitor(self, root: Path) -> CityMonitor:
        monitor = CityMonitor(
            ProviderConfig(
                city="Berlin",
                provider="dp-document-berlin",
                queue_url="https://berlin.pasport.org.ua/solutions/e-queue",
                env_prefix="TEST_BERLIN",
                base_dir=root,
                project_dir=root,
            )
        )
        monitor.data_dir = root / "data"
        monitor.metadata_dir = root / "metadata"
        monitor.state_file = monitor.data_dir / "berlin_state.json"
        monitor.metadata_file = monitor.metadata_dir / "berlin.jsonl"
        return monitor

    def test_each_check_appends_standard_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            monitor = self.make_monitor(Path(directory))
            with patch.object(
                monitor,
                "fetch_page",
                return_value=(
                    200,
                    "Наразі всі місця зайняті "
                    "Будь ласка, спробуйте в інший час або день",
                ),
            ):
                result = monitor.check_once()

            record = json.loads(
                monitor.metadata_file.read_text(encoding="utf-8").splitlines()[0]
            )
            self.assertEqual(result.status, "NO_SLOTS")
            self.assertEqual(
                set(record),
                {
                    "schema_version",
                    "observation_id",
                    "run_id",
                    "provider_id",
                    "observed_at",
                    "duration_ms",
                    "page_hash",
                    "classifier_reason",
                    "error_category",
                    "discovery_stage",
                    "evidence",
                    "request_trace",
                    "available_dates_count",
                    "available_time_slots_count",
                    "earliest_available_time",
                    "latest_available_time",
                    "state",
                    "transport",
                    "html_changed",
                    "http_status",
                },
            )
            self.assertEqual(record["schema_version"], 3)
            self.assertEqual(record["provider_id"], "dp-document-berlin")
            self.assertEqual(record["http_status"], 200)
            self.assertFalse(record["html_changed"])
            self.assertEqual(record["discovery_stage"], "LANDING")
            self.assertEqual(len(record["request_trace"]), 1)

    def test_playwright_fallback_accepts_all_governed_discovery_profiles(self) -> None:
        profiles = {
            "madrid-v1",
            "barcelona-v1",
            "london-research-v1",
            "milan-research-v1",
            "valencia-v1",
            "berlin-v1",
            "bratislava-v1",
            "toronto-v1",
            "cologne-v1",
            "prague-v1",
            "varna-v1",
            "chisinau-v1",
            "kortrijk-v1",
            "warsaw-v1",
            "krakow-v1",
            "gdansk-v1",
            "wroclaw-v1",
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ",
            {"PLAYWRIGHT_DISCOVERY_FALLBACK_ENABLED": "true"},
        ):
            for profile in profiles:
                monitor = CityMonitor(
                    ProviderConfig(
                        city="Test",
                        provider="dp-document-test",
                        queue_url="https://example.test/solutions/e-queue",
                        env_prefix="TEST_PROFILE",
                        base_dir=Path(directory),
                        public_discovery_profile=profile,
                    )
                )
                self.assertTrue(
                    monitor.playwright_fallback_enabled(),
                    profile,
                )

    def test_second_different_page_marks_html_changed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            monitor = self.make_monitor(Path(directory))
            with patch.object(
                monitor,
                "fetch_page",
                side_effect=[
                    (
                        200,
                        "Наразі всі місця зайняті "
                        "Будь ласка, спробуйте в інший час або день",
                    ),
                    (200, "<html>changed</html>"),
                ],
            ):
                monitor.check_once()
                monitor.check_once()

            records = [
                json.loads(line)
                for line in monitor.metadata_file.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertFalse(records[0]["html_changed"])
            self.assertTrue(records[1]["html_changed"])

    def test_unconfirmed_http_form_writes_sanitized_candidate_artifact(
        self,
    ) -> None:
        landing_html = """
        <form x-data='qlogicFormTotoro({"center":"15","csrf":"SECRET_FIELD"})'>
          <select name="service">
            <option value="">Choose</option>
            <option value="4">Passport service</option>
            <option value="7">Another public service</option>
          </select>
          <select name="date"><option value="">Choose</option></select>
        </form>
        """
        with tempfile.TemporaryDirectory() as directory:
            monitor = self.make_monitor(Path(directory))
            with patch.object(
                monitor, "fetch_page", return_value=(200, landing_html)
            ):
                state = monitor.check_once()

            artifact = json.loads(
                monitor.candidate_evidence.artifact_path.read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(state.status, "UNKNOWN")
        self.assertEqual(state.discovery_stage, "LANDING")
        self.assertIn("SERVICE_SELECTOR_FOUND", state.evidence)
        self.assertIn("SERVICE_OPTIONS_FOUND", state.evidence)
        self.assertEqual(artifact["service_center_id"], "15")
        self.assertEqual(
            [item["service_id"] for item in artifact["options"]],
            ["4", "7"],
        )
        self.assertNotIn("SECRET_FIELD", json.dumps(artifact))

    def test_blocked_candidate_probe_runs_once_for_same_page_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monitor = CityMonitor(
                ProviderConfig(
                    city="Berlin",
                    provider="dp-document-berlin",
                    queue_url="https://example.test/solutions/e-queue",
                    env_prefix="TEST_BERLIN",
                    base_dir=root,
                    project_dir=root,
                    candidate_evidence_probe=True,
                )
            )
            browser_state = QueueState(
                "UNKNOWN",
                "2026-08-01T10:00:00+00:00",
                "browser-page-hash",
                "Candidate queue form detected; governance review required.",
                "playwright",
                ("QUEUE_FORM_FOUND", "SERVICE_OPTIONS_FOUND"),
                "LANDING",
            )
            with (
                patch.dict(
                    "os.environ",
                    {"CANDIDATE_EVIDENCE_PROBE_ENABLED": "true"},
                ),
                patch.object(
                    monitor,
                    "fetch_page",
                    return_value=(403, "stable challenge"),
                ),
                patch.object(
                    monitor,
                    "run_browser_candidate_probe",
                    return_value=(browser_state, 200),
                ) as probe,
            ):
                monitor.check_once()
                monitor.check_once()

        probe.assert_called_once()

    def test_provider_entrypoints_have_distinct_contracts(self) -> None:
        providers = {}
        cities = (
            "berlin",
            "bratislava",
            "kortrijk",
            "madrid",
            "london",
            "milan",
            "toronto",
            "chisinau",
            "barcelona",
            "valencia",
            "cologne",
            "prague",
            "varna",
            "warsaw",
            "krakow",
            "gdansk",
            "wroclaw",
        )
        for city in cities:
            spec = importlib.util.spec_from_file_location(
                f"{city}_monitor_test",
                PROVIDER_DIR / f"{city}_monitor.py",
            )
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            providers[city] = module.MONITOR.config

        self.assertEqual(len({item.provider for item in providers.values()}), len(cities))
        self.assertEqual(len({item.queue_url for item in providers.values()}), len(cities))

    def test_registry_defines_research_sample_without_protocol_changes(self) -> None:
        providers = load_provider_registry()

        self.assertEqual(
            set(providers),
            {
                "berlin",
                "bratislava",
                "kortrijk",
                "madrid",
                "london",
                "milan",
                "toronto",
                "chisinau",
                "barcelona",
                "valencia",
                "cologne",
                "prague",
                "varna",
                "warsaw",
                "krakow",
                "gdansk",
                "wroclaw",
            },
        )
        self.assertTrue(all(item.enabled for item in providers.values()))
        self.assertEqual(providers["bratislava"].priority, "high")
        self.assertEqual(providers["madrid"].observation_group, "active")
        self.assertEqual(
            providers["madrid"].monitor.public_discovery_profile,
            "madrid-v1",
        )
        self.assertEqual(providers["madrid"].monitor.service_center_id, "6")
        self.assertEqual(providers["madrid"].monitor.service_id, "4")
        self.assertEqual(
            providers["barcelona"].monitor.public_discovery_profile,
            "barcelona-v1",
        )
        self.assertEqual(
            providers["barcelona"].monitor.service_center_id, "41"
        )
        self.assertEqual(providers["barcelona"].monitor.service_id, "4")
        self.assertEqual(
            providers["barcelona"].observation_group, "active"
        )
        self.assertEqual(
            providers["london"].monitor.public_discovery_profile,
            "london-research-v1",
        )
        self.assertEqual(
            providers["milan"].monitor.public_discovery_profile,
            "milan-research-v1",
        )
        self.assertEqual(providers["london"].monitor.service_center_id, "47")
        self.assertEqual(providers["london"].monitor.service_id, "4")
        self.assertEqual(providers["milan"].monitor.service_center_id, "4")
        self.assertEqual(providers["milan"].monitor.service_id, "4")
        self.assertEqual(
            providers["valencia"].monitor.public_discovery_profile,
            "valencia-v1",
        )
        self.assertEqual(providers["valencia"].monitor.service_center_id, "7")
        self.assertEqual(providers["valencia"].monitor.service_id, "4")
        self.assertEqual(providers["valencia"].observation_group, "active")
        self.assertEqual(providers["toronto"].observation_group, "control")
        self.assertEqual(
            providers["berlin"].monitor.public_discovery_profile,
            "berlin-v1",
        )
        self.assertEqual(providers["berlin"].monitor.service_center_id, "2")
        self.assertEqual(
            providers["bratislava"].monitor.public_discovery_profile,
            "bratislava-v1",
        )
        self.assertEqual(
            providers["bratislava"].monitor.service_center_id,
            "9",
        )
        self.assertEqual(
            providers["toronto"].monitor.public_discovery_profile,
            "toronto-v1",
        )
        self.assertEqual(providers["toronto"].monitor.service_center_id, "46")
        self.assertEqual(
            providers["cologne"].monitor.public_discovery_profile,
            "cologne-v1",
        )
        self.assertEqual(providers["cologne"].monitor.service_center_id, "3")
        self.assertEqual(providers["cologne"].monitor.service_id, "4")
        self.assertEqual(
            providers["prague"].monitor.public_discovery_profile,
            "prague-v1",
        )
        self.assertEqual(providers["prague"].monitor.service_center_id, "8")
        self.assertEqual(providers["prague"].monitor.service_id, "4")
        self.assertEqual(providers["prague"].observation_group, "active")
        self.assertEqual(
            providers["varna"].monitor.public_discovery_profile,
            "varna-v1",
        )
        self.assertEqual(
            providers["chisinau"].monitor.public_discovery_profile,
            "chisinau-v1",
        )
        self.assertEqual("45", providers["chisinau"].monitor.service_center_id)
        self.assertEqual("4", providers["chisinau"].monitor.service_id)
        self.assertEqual(providers["varna"].monitor.service_center_id, "43")
        self.assertEqual(providers["varna"].monitor.service_id, "4")
        self.assertEqual(providers["varna"].observation_group, "active")
        self.assertEqual(providers["chisinau"].observation_group, "control")
        expected_poland = {
            "warsaw": ("warsaw-v1", "10"),
            "krakow": ("krakow-v1", "11"),
            "gdansk": ("gdansk-v1", "12"),
            "wroclaw": ("wroclaw-v1", "13"),
        }
        for city, (profile, centre) in expected_poland.items():
            self.assertEqual(providers[city].monitor.public_discovery_profile, profile)
            self.assertEqual(providers[city].monitor.service_center_id, centre)
            self.assertEqual(providers[city].monitor.service_id, "4")
            self.assertEqual(providers[city].observation_group, "active")
        self.assertEqual(
            providers["kortrijk"].monitor.public_discovery_profile,
            "kortrijk-v1",
        )
        self.assertEqual("48", providers["kortrijk"].monitor.service_center_id)
        self.assertEqual("4", providers["kortrijk"].monitor.service_id)
        self.assertEqual(providers["kortrijk"].observation_group, "control")
        self.assertTrue(
            providers["berlin"].monitor.candidate_evidence_probe
        )
        self.assertFalse(providers["kortrijk"].monitor.candidate_evidence_probe)
        self.assertFalse(
            providers["bratislava"].monitor.candidate_evidence_probe
        )
        self.assertTrue(all(item.entrypoint.is_file() for item in providers.values()))
        self.assertEqual(
            [item.startup_delay_seconds for item in providers.values()],
            [
                0,
                30,
                60,
                90,
                120,
                150,
                180,
                210,
                240,
                270,
                300,
                330,
                360,
                390,
                420,
                450,
                480,
            ],
        )

    def test_runner_can_select_research_cohort_from_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {"MONITOR_PROVIDER_CITIES": "madrid, london, milan"},
        ):
            providers = configured_providers()

        self.assertEqual(set(providers), {"Madrid", "London", "Milan"})

    def test_runner_can_select_confirmed_positive_control_pair(self) -> None:
        with patch.dict(
            "os.environ",
            {"MONITOR_PROVIDER_CITIES": "madrid, barcelona"},
        ):
            providers = configured_providers()

        self.assertEqual(set(providers), {"Madrid", "Barcelona"})

    def test_runner_can_select_four_centre_browser_cohort(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "MONITOR_PROVIDER_CITIES": (
                    "madrid,barcelona,london,milan"
                )
            },
        ):
            providers = configured_providers()

        self.assertEqual(
            set(providers),
            {"Madrid", "Barcelona", "London", "Milan"},
        )

    def test_runner_can_select_five_centre_browser_cohort(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "MONITOR_PROVIDER_CITIES": (
                    "madrid,barcelona,london,milan,valencia"
                )
            },
        ):
            providers = configured_providers()

        self.assertEqual(
            set(providers),
            {"Madrid", "Barcelona", "London", "Milan", "Valencia"},
        )

    def test_runner_rejects_unknown_research_city(self) -> None:
        with patch.dict(
            "os.environ",
            {"MONITOR_PROVIDER_CITIES": "madrid, unknown"},
        ):
            with self.assertRaisesRegex(ValueError, "unknown"):
                configured_providers()

    def test_runner_accepts_positive_bounded_duration(self) -> None:
        with patch.dict(
            "os.environ",
            {"MONITOR_RUN_DURATION_SECONDS": "21600"},
        ):
            self.assertEqual(configured_run_duration_seconds(), 21600)

    def test_runner_rejects_non_positive_bounded_duration(self) -> None:
        with patch.dict(
            "os.environ",
            {"MONITOR_RUN_DURATION_SECONDS": "0"},
        ):
            with self.assertRaisesRegex(ValueError, "must be positive"):
                configured_run_duration_seconds()

    def test_runner_generates_summary_for_completed_long_run(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="E:\\reports\\runtime-report.md\n",
            stderr="",
        )
        with patch.dict("os.environ", {}, clear=True), patch(
            "monitor_runner.subprocess.run", return_value=completed
        ) as run:
            report = generate_research_summary(
                "RUN-test",
                run_started_at=datetime(2026, 8, 1, 10, tzinfo=timezone.utc),
                run_ended_at=datetime(2026, 8, 1, 22, tzinfo=timezone.utc),
            )

        self.assertEqual(report, Path("E:\\reports\\runtime-report.md"))
        command = run.call_args.args[0]
        self.assertIn("--run-id", command)
        self.assertIn("RUN-test", command)
        self.assertIn("--minimum-duration-hours", command)
        self.assertIn("--run-started-at", command)
        self.assertIn("--run-ended-at", command)

    def test_runner_skips_summary_when_disabled(self) -> None:
        with patch.dict(
            "os.environ", {"RESEARCH_SUMMARY_ENABLED": "false"}
        ), patch("monitor_runner.subprocess.run") as run:
            report = generate_research_summary(
                "RUN-test",
                run_started_at=datetime(2026, 8, 1, 10, tzinfo=timezone.utc),
                run_ended_at=datetime(2026, 8, 1, 22, tzinfo=timezone.utc),
            )

        self.assertIsNone(report)
        run.assert_not_called()

    def test_madrid_runtime_stops_after_confirmed_times(self) -> None:
        landing_html = """
        <form
          x-data='qlogicFormTotoro({
            "csrf": "TEST_OPAQUE_FIELD_NAME_NOT_SECRET",
            "center": "6"
          })'
        >
          <select name="service">
            <option value="">Select</option>
            <option value="4">Confirmed service</option>
          </select>
        </form>
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monitor = CityMonitor(
                ProviderConfig(
                    city="Madrid",
                    provider="dp-document-madrid",
                    queue_url="https://example.test/solutions/e-queue",
                    env_prefix="TEST_MADRID",
                    base_dir=root,
                    project_dir=root,
                    public_discovery_profile="madrid-v1",
                    service_center_id="6",
                    service_id="4",
                    csrf_value="1",
                )
            )
            responses = [
                (
                    200,
                    {
                        "days": [
                            {
                                "datePart": "2026-08-03",
                                "date": "03.08.2026",
                                "isAllowed": True,
                            }
                        ]
                    },
                    10,
                    100,
                ),
                (
                    200,
                    {
                        "timeSlots": [
                            {
                                "startTime": "12:40:00",
                                "slot": "12:40 — 1 вільний слот",
                                "isAllowed": True,
                            },
                            {
                                "startTime": "18:40:00",
                                "slot": "18:40 — 3 вільні слоти",
                                "isAllowed": True,
                            },
                        ]
                    },
                    11,
                    200,
                ),
            ]
            with patch.object(
                monitor,
                "_post_public_discovery",
                side_effect=responses,
            ) as post:
                state = monitor.discover_public_availability(
                    landing_status=200,
                    landing_html=landing_html,
                    landing_trace=RequestTraceEntry(
                        "GET", "landing", 200, 9, 300
                    ),
                )

        self.assertEqual(state.status, "SLOTS_AVAILABLE")
        self.assertEqual(state.discovery_stage, "TIMES")
        self.assertEqual(state.available_dates_count, 1)
        self.assertEqual(state.available_time_slots_count, 2)
        self.assertEqual(state.earliest_available_time, "12:40:00")
        self.assertEqual(state.latest_available_time, "18:40:00")
        self.assertEqual(
            [call.kwargs["form"] for call in post.call_args_list],
            ["days", "times"],
        )
        self.assertEqual(
            post.call_args_list[0].kwargs["fields"],
            {
                "ServiceCenterId": "6",
                "ServiceId": "4",
                "TEST_OPAQUE_FIELD_NAME_NOT_SECRET": "1",
            },
        )
        self.assertEqual(
            post.call_args_list[1].kwargs["fields"]["Date"],
            "2026-08-03",
        )
        self.assertEqual(
            [entry.operation for entry in state.request_trace],
            ["landing", "days", "times"],
        )

    def test_madrid_runtime_fails_closed_on_unrecognized_times(self) -> None:
        landing_html = """
        <form
          x-data='qlogicFormTotoro({
            "csrf": "TEST_OPAQUE_FIELD_NAME_NOT_SECRET",
            "center": "6"
          })'
        >
          <select name="service">
            <option value="4">Confirmed service</option>
          </select>
        </form>
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monitor = CityMonitor(
                ProviderConfig(
                    city="Madrid",
                    provider="dp-document-madrid",
                    queue_url="https://example.test/solutions/e-queue",
                    env_prefix="TEST_MADRID",
                    base_dir=root,
                    project_dir=root,
                    public_discovery_profile="madrid-v1",
                    service_center_id="6",
                    service_id="4",
                    csrf_value="1",
                )
            )
            with patch.object(
                monitor,
                "_post_public_discovery",
                side_effect=[
                    (
                        200,
                        {
                            "days": [
                                {
                                    "datePart": "2026-08-03",
                                    "date": "03.08.2026",
                                    "isAllowed": True,
                                }
                            ]
                        },
                        10,
                        100,
                    ),
                    (200, {"unexpected": []}, 11, 20),
                ],
            ):
                state = monitor.discover_public_availability(
                    landing_status=200,
                    landing_html=landing_html,
                    landing_trace=RequestTraceEntry(
                        "GET", "landing", 200, 9, 300
                    ),
                )

        self.assertEqual(state.status, "UNKNOWN")
        self.assertEqual(state.discovery_stage, "TIMES")
        self.assertEqual(state.available_time_slots_count, None)
        self.assertIn("TIMES_PAYLOAD_UNRECOGNIZED", state.evidence)

    def test_barcelona_profile_uses_confirmed_centre_and_stops_at_times(
        self,
    ) -> None:
        landing_html = """
        <form
          x-data='qlogicFormTotoro({
            "csrf": "TEST_DYNAMIC_FIELD_NOT_SECRET",
            "center": "41"
          })'
        >
          <select name="service">
            <option value="4">Confirmed service</option>
          </select>
        </form>
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monitor = CityMonitor(
                ProviderConfig(
                    city="Barcelona",
                    provider="dp-document-barcelona",
                    queue_url="https://example.test/solutions/e-queue",
                    env_prefix="TEST_BARCELONA",
                    base_dir=root,
                    project_dir=root,
                    public_discovery_profile="barcelona-v1",
                    service_center_id="41",
                    service_id="4",
                    csrf_value="1",
                )
            )
            with patch.object(
                monitor,
                "_post_public_discovery",
                side_effect=[
                    (
                        200,
                        {
                            "days": [
                                {
                                    "datePart": "2026-08-04",
                                    "date": "04.08.2026",
                                    "isAllowed": True,
                                }
                            ]
                        },
                        10,
                        100,
                    ),
                    (
                        200,
                        {
                            "timeSlots": [
                                {
                                    "startTime": "12:30:00",
                                    "slot": "12:30 — 1 вільний слот",
                                    "isAllowed": True,
                                }
                            ]
                        },
                        11,
                        100,
                    ),
                ],
            ) as post:
                state = monitor.discover_public_availability(
                    landing_status=200,
                    landing_html=landing_html,
                    landing_trace=RequestTraceEntry(
                        "GET", "landing", 200, 9, 300
                    ),
                )

        self.assertEqual(state.status, "SLOTS_AVAILABLE")
        self.assertEqual(state.discovery_stage, "TIMES")
        self.assertEqual(state.available_dates_count, 1)
        self.assertEqual(state.available_time_slots_count, 1)
        self.assertEqual(
            post.call_args_list[0].kwargs["fields"],
            {
                "ServiceCenterId": "41",
                "ServiceId": "4",
                "TEST_DYNAMIC_FIELD_NOT_SECRET": "1",
            },
        )
        self.assertEqual(len(post.call_args_list), 2)

    def test_http_success_does_not_start_playwright_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            monitor = self.make_monitor(Path(directory))
            with (
                patch.object(
                    monitor,
                    "fetch_page",
                    return_value=(200, "Наразі всі місця зайняті"),
                ),
                patch.object(monitor, "run_browser_fallback") as fallback,
            ):
                state = monitor.check_once()

        self.assertEqual(state.source, "http")
        fallback.assert_not_called()

    def test_blocked_confirmed_provider_switches_to_playwright(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            monitor = CityMonitor(
                ProviderConfig(
                    city="Barcelona",
                    provider="dp-document-barcelona",
                    queue_url="https://example.test/solutions/e-queue",
                    env_prefix="TEST_BARCELONA",
                    base_dir=root,
                    project_dir=root,
                    public_discovery_profile="barcelona-v1",
                    service_center_id="41",
                    service_id="4",
                    csrf_value="1",
                )
            )
            browser_state = QueueState(
                "SLOTS_AVAILABLE",
                "2026-07-31T10:00:00+00:00",
                "browser-page-hash",
                "Available dates: 1; available time slots: 2; "
                "earliest: 12:30:00; latest: 13:00:00.",
                "playwright",
                ("AVAILABLE_DATES_FOUND", "AVAILABLE_TIMES_FOUND"),
                "TIMES",
                1,
                2,
                "12:30:00",
                "13:00:00",
                (
                    RequestTraceEntry(
                        "GET", "landing", 403, 50, 500, transport="http"
                    ),
                    RequestTraceEntry(
                        "GET",
                        "landing",
                        200,
                        500,
                        5000,
                        transport="playwright",
                    ),
                    RequestTraceEntry(
                        "POST",
                        "days",
                        200,
                        100,
                        200,
                        transport="playwright",
                    ),
                    RequestTraceEntry(
                        "POST",
                        "times",
                        200,
                        100,
                        300,
                        transport="playwright",
                    ),
                ),
            )
            with (
                patch.object(
                    monitor,
                    "fetch_page",
                    return_value=(403, "Cloudflare challenge"),
                ),
                patch.object(
                    monitor,
                    "playwright_fallback_enabled",
                    return_value=True,
                ),
                patch.object(
                    monitor,
                    "run_browser_fallback",
                    return_value=(browser_state, 200),
                ) as fallback,
            ):
                state = monitor.check_once()

            record = json.loads(
                monitor.metadata_file.read_text(encoding="utf-8").splitlines()[0]
            )

        fallback.assert_called_once()
        self.assertEqual(state.source, "playwright")
        self.assertEqual(record["transport"], "playwright")
        self.assertEqual(record["http_status"], 200)
        self.assertEqual(record["discovery_stage"], "TIMES")
        self.assertEqual(record["available_dates_count"], 1)
        self.assertEqual(record["available_time_slots_count"], 2)
        self.assertEqual(
            [item["transport"] for item in record["request_trace"]],
            ["http", "playwright", "playwright", "playwright"],
        )


if __name__ == "__main__":
    unittest.main()
