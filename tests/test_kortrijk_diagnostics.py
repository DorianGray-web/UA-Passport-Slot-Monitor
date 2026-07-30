from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
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


def state(
    status: str,
    page_hash: str,
    message: str = "message",
) -> object:
    return monitor.QueueState(status, "now", page_hash, message, "http")


class DiagnosticTriggerTests(unittest.TestCase):
    def test_ctrl_c_is_logged_as_manual_monitor_stop(self) -> None:
        with patch.object(
            monitor, "configure_logging"
        ), patch.object(
            monitor, "run_monitor", side_effect=KeyboardInterrupt
        ), self.assertLogs(level="INFO") as captured:
            exit_code = monitor.main()

        self.assertEqual(exit_code, 130)
        self.assertIn(
            "Monitoring stopped manually. "
            "reason=manual_interrupt signal=Ctrl+C",
            captured.output[0],
        )

    def test_transition_log_has_reason_and_diagnostic_fields(self) -> None:
        previous = state("NO_SLOTS", "before")
        current = state(
            "CAPTCHA_REQUIRED",
            "after",
            "Visible reCAPTCHA widget detected.",
        )

        with self.assertLogs(level="WARNING") as captured:
            monitor.report_change(
                previous,
                current,
                ["CAPTCHA_REQUIRED"],
                diagnostic_backend_available=True,
            )

        message = captured.output[0]
        self.assertIn("NO_SLOTS -> CAPTCHA_REQUIRED", message)
        self.assertIn(
            "reason=Visible reCAPTCHA widget detected.",
            message,
        )
        self.assertIn("diagnostic=triggered", message)
        self.assertIn("diagnostic_events=CAPTCHA_REQUIRED", message)

    def test_recovery_transition_explains_restored_queue_page(self) -> None:
        reason = monitor.transition_reason(
            state("CAPTCHA_REQUIRED", "before"),
            state(
                "NO_SLOTS",
                "after",
                "Official no-slots message detected.",
            ),
        )

        self.assertEqual(
            reason,
            "Queue page restored to recognized state NO_SLOTS. "
            "Official no-slots message detected.",
        )

    def test_repeated_same_state_does_not_trigger(self) -> None:
        events = monitor.diagnostic_events_for_transition(
            state("BLOCKED", "same"),
            state("BLOCKED", "same"),
            {"BLOCKED"},
        )
        self.assertEqual(events, [])

    def test_transition_into_configured_state_triggers_once(self) -> None:
        events = monitor.diagnostic_events_for_transition(
            state("NO_SLOTS", "before"),
            state("UNKNOWN", "after"),
            {"UNKNOWN"},
        )
        self.assertEqual(events, ["UNKNOWN"])

    def test_same_state_hash_change_maps_to_structure_event(self) -> None:
        events = monitor.diagnostic_events_for_transition(
            state("NO_SLOTS", "before"),
            state("NO_SLOTS", "after"),
            {"HTML_STRUCTURE_CHANGED"},
        )
        self.assertEqual(events, ["HTML_STRUCTURE_CHANGED"])

    def test_disabled_event_does_not_trigger(self) -> None:
        events = monitor.diagnostic_events_for_transition(
            None,
            state("BLOCKED", "hash"),
            set(),
        )
        self.assertEqual(events, [])

    def test_explicit_empty_configuration_stays_disabled(self) -> None:
        class Backend:
            def investigate(self, request: object) -> object:
                raise AssertionError("disabled backend must not be invoked")

        with patch.object(
            monitor, "load_previous_state", return_value=state("BLOCKED", "same")
        ), patch.object(
            monitor, "fetch_page", return_value=(403, "blocked")
        ), patch.object(
            monitor, "save_state"
        ):
            monitor.check_once(Backend(), set())


if __name__ == "__main__":
    unittest.main()
