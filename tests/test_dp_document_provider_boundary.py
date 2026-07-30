from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROVIDER_DIR = PROJECT_DIR / "providers" / "dp-document"
sys.path.insert(0, str(PROVIDER_DIR))

from dp_document_http import DPDocumentHTTPMonitorProvider  # noqa: E402
from provider_boundaries import DaysRequest, TimesRequest  # noqa: E402
from provider_protocol import (  # noqa: E402
    EvidenceCode,
    DiscoveryEngine,
    DiscoveryStage,
    LandingPageClassifier,
    LandingState,
    TransitionGuard,
)


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = (
            '<meta name="csrf-token" content="TEST_CSRF_VALUE_NOT_SECRET">'
        )

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self) -> None:
        self.posts: list[dict[str, Any]] = []

    def get(self, *args: Any, **kwargs: Any) -> FakeResponse:
        return FakeResponse({})

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse({"ok": True})


class DPDocumentMonitorProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = FakeSession()
        self.provider = DPDocumentHTTPMonitorProvider(
            provider_id="dp-document-berlin",
            queue_url="https://example.test/solutions/e-queue",
            csrf_field="csrf",
            session=self.session,  # type: ignore[arg-type]
        )

    def test_days_request_contains_only_confirmed_monitoring_fields(self) -> None:
        self.provider.get_days(
            DaysRequest("TEST_CENTRE", "TEST_SERVICE", "TEST_CSRF_VALUE_NOT_SECRET")
        )
        payload = self.session.posts[0]["data"]
        self.assertEqual(
            payload,
            {
                "form": "days",
                "ServiceCenterId": "TEST_CENTRE",
                "ServiceId": "TEST_SERVICE",
                "csrf": "TEST_CSRF_VALUE_NOT_SECRET",
            },
        )
        self.assertNotIn("fingerprint", payload)

    def test_times_adds_date_without_fingerprint(self) -> None:
        self.provider.get_times(
            TimesRequest(
                "TEST_CENTRE",
                "TEST_SERVICE",
                "2099-01-01",
                "TEST_CSRF_VALUE_NOT_SECRET",
            )
        )
        payload = self.session.posts[0]["data"]
        self.assertEqual(payload["form"], "times")
        self.assertEqual(payload["Date"], "2099-01-01")
        self.assertNotIn("fingerprint", payload)

    def test_csrf_is_loaded_over_http_without_browser(self) -> None:
        self.assertEqual(
            self.provider.load_csrf_token(),
            "TEST_CSRF_VALUE_NOT_SECRET",
        )

    def test_runtime_monitors_do_not_import_browser_automation(self) -> None:
        for filename in ("city_monitor.py", "kortrijk_monitor.py"):
            source = (PROVIDER_DIR / filename).read_text(encoding="utf-8")
            self.assertNotIn("playwright", source.lower())
            self.assertNotIn("fingerprint", source.lower())
            self.assertNotIn("browser_fallback", source)

    def test_confirmed_html_marker_stops_at_landing(self) -> None:
        result = LandingPageClassifier().classify(
            200, "<main>Наразі всі місця зайняті</main>"
        )
        self.assertEqual(result.state, LandingState.NO_SLOTS)
        self.assertIn(EvidenceCode.HTML_NO_SLOTS_MARKER, result.evidence)
        self.assertFalse(TransitionGuard.allows_days(result))

    def test_valid_form_and_csrf_allow_days_transition(self) -> None:
        result = LandingPageClassifier("csrf").classify(
            200,
            """
            <form>
              <input name="csrf" value="TEST_CSRF_VALUE_NOT_SECRET">
              <input name="ServiceCenterId" value="TEST_CENTRE">
              <input name="ServiceId" value="TEST_SERVICE">
            </form>
            """,
        )
        self.assertEqual(result.state, LandingState.DISCOVERY_READY)
        self.assertTrue(TransitionGuard.allows_days(result))
        self.assertEqual(
            DiscoveryEngine.next_stage_after_landing(result),
            DiscoveryStage.SERVICE_VALIDATION,
        )
        assert result.queue_form is not None
        self.assertEqual(result.queue_form.service_center_id, "TEST_CENTRE")
        self.assertEqual(result.queue_form.service_id, "TEST_SERVICE")

    def test_blocked_page_never_becomes_no_slots(self) -> None:
        result = LandingPageClassifier().classify(
            403, "Наразі всі місця зайняті"
        )
        self.assertEqual(result.state, LandingState.BLOCKED)
        self.assertNotIn(EvidenceCode.HTML_NO_SLOTS_MARKER, result.evidence)

    def test_times_transition_requires_confirmed_dates(self) -> None:
        self.assertIsNone(DiscoveryEngine.next_stage_after_days(()))
        self.assertEqual(
            DiscoveryEngine.next_stage_after_days(("2026-08-01",)),
            DiscoveryStage.TIMES,
        )


if __name__ == "__main__":
    unittest.main()
