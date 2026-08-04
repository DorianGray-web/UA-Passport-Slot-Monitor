from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROVIDER_DIR = PROJECT_DIR / "providers" / "dp-document"
sys.path.insert(0, str(PROVIDER_DIR))
spec = importlib.util.spec_from_file_location(
    "kortrijk_monitor", PROVIDER_DIR / "kortrijk_monitor.py"
)
assert spec and spec.loader
monitor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = monitor
spec.loader.exec_module(monitor)


class KortrijkEntrypointTests(unittest.TestCase):
    def test_entrypoint_uses_shared_city_monitor(self) -> None:
        self.assertEqual(monitor.MONITOR.config.city, "Kortrijk")
        self.assertEqual(
            monitor.MONITOR.config.provider,
            "dp-document-kortrijk",
        )
        self.assertEqual(
            monitor.MONITOR.config.public_discovery_profile,
            "kortrijk-v1",
        )
        self.assertFalse(monitor.MONITOR.config.candidate_evidence_probe)

    def test_ctrl_c_is_logged_as_manual_monitor_stop(self) -> None:
        with patch.object(
            monitor.MONITOR, "configure_logging"
        ), patch.object(
            monitor.MONITOR, "run", side_effect=KeyboardInterrupt
        ), self.assertLogs(level="INFO") as captured:
            exit_code = monitor.MONITOR.main()

        self.assertEqual(exit_code, 130)
        self.assertIn(
            "Monitoring stopped manually. "
            "reason=manual_interrupt signal=Ctrl+C",
            captured.output[0],
        )


if __name__ == "__main__":
    unittest.main()
