from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROVIDER_DIR = PROJECT_DIR / "providers" / "dp-document"
sys.path.insert(0, str(PROVIDER_DIR))

from city_monitor import CityMonitor, ProviderConfig  # noqa: E402


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
                    "state",
                    "transport",
                    "html_changed",
                    "http_status",
                },
            )
            self.assertEqual(record["schema_version"], 2)
            self.assertEqual(record["provider_id"], "dp-document-berlin")
            self.assertEqual(record["http_status"], 200)
            self.assertFalse(record["html_changed"])
            self.assertEqual(record["discovery_stage"], "LANDING")
            self.assertEqual(len(record["request_trace"]), 1)

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

    def test_provider_entrypoints_have_distinct_contracts(self) -> None:
        providers = {}
        for city in ("berlin", "bratislava"):
            spec = importlib.util.spec_from_file_location(
                f"{city}_monitor_test",
                PROVIDER_DIR / f"{city}_monitor.py",
            )
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            providers[city] = module.MONITOR.config

        self.assertNotEqual(providers["berlin"].provider, providers["bratislava"].provider)
        self.assertNotEqual(providers["berlin"].queue_url, providers["bratislava"].queue_url)


if __name__ == "__main__":
    unittest.main()
