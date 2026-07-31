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
    ConfirmedDaysClassifier,
    ConfirmedTimesClassifier,
    TransitionGuard,
)


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = (
            '<meta name="csrf-token" content="TEST_CSRF_VALUE_NOT_SECRET">'
        )
        self.content = self.text.encode("utf-8")

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
            self.assertNotIn("fingerprint", source.lower())
        city_source = (PROVIDER_DIR / "city_monitor.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("sync_playwright", city_source)
        kortrijk_source = (PROVIDER_DIR / "kortrijk_monitor.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("browser_fallback", kortrijk_source)

    def test_browser_transport_has_no_identity_or_booking_actions(self) -> None:
        source = (PROVIDER_DIR / "browser_discovery.py").read_text(
            encoding="utf-8"
        ).lower()
        self.assertIn("launch_persistent_context", source)
        self.assertNotIn("fingerprint", source)
        self.assertNotIn("proxy=", source)
        for forbidden_selector in (
            "first_name",
            "last_name",
            "phone",
            "submitform",
            'click("',
            ".click(",
        ):
            self.assertNotIn(forbidden_selector, source)

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

    def test_booking_hcaptcha_asset_does_not_block_public_discovery(self) -> None:
        result = LandingPageClassifier("csrf").classify(
            200,
            """
            <form id="form">
              <input name="csrf" value="TEST_CSRF_VALUE_NOT_SECRET">
              <input name="ServiceCenterId" value="TEST_CENTRE">
              <input name="ServiceId" value="TEST_SERVICE">
              <script src="https://js.hcaptcha.com/1/api.js"></script>
              <div class="h-captcha"></div>
            </form>
            """,
        )
        self.assertEqual(result.state, LandingState.DISCOVERY_READY)
        self.assertNotIn(EvidenceCode.CHALLENGE_MARKER, result.evidence)
        self.assertTrue(TransitionGuard.allows_days(result))

    def test_madrid_style_embedded_config_allows_public_discovery(self) -> None:
        result = LandingPageClassifier().classify(
            200,
            """
            <form
              id="form"
              name="services"
              x-data='qlogicFormTotoro({
                "url": "https://example.invalid/solutions/e-queue",
                "csrf": "TEST_OPAQUE_FIELD_NAME_NOT_SECRET",
                "center": "6",
                "hcaptcha": "TEST_PUBLIC_SITE_KEY"
              })'
            >
              <select id="service" name="service">
                <option value="">Select</option>
                <option value="4" selected>Test service</option>
              </select>
              <script src="https://js.hcaptcha.com/1/api.js"></script>
            </form>
            """,
        )
        self.assertEqual(result.state, LandingState.DISCOVERY_READY)
        self.assertEqual(
            result.csrf_token, "TEST_OPAQUE_FIELD_NAME_NOT_SECRET"
        )
        assert result.queue_form is not None
        self.assertEqual(result.queue_form.service_center_id, "6")
        self.assertEqual(result.queue_form.service_id, "4")
        self.assertTrue(TransitionGuard.allows_days(result))
        self.assertEqual(
            LandingPageClassifier.confirmed_public_form_csrf_field(
                """
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
                """,
                service_center_id="6",
                service_id="4",
            ),
            "TEST_OPAQUE_FIELD_NAME_NOT_SECRET",
        )

    def test_madrid_guard_rejects_unconfirmed_service(self) -> None:
        self.assertIsNone(
            LandingPageClassifier.confirmed_public_form_csrf_field(
                """
                <form
                  x-data='qlogicFormTotoro({
                    "csrf": "TEST_OPAQUE_FIELD_NAME_NOT_SECRET",
                    "center": "6"
                  })'
                >
                  <select name="service">
                    <option value="99">Different service</option>
                  </select>
                </form>
                """,
                service_center_id="6",
                service_id="4",
            )
        )

    def test_browser_form_guard_does_not_require_exposed_csrf(self) -> None:
        self.assertTrue(
            LandingPageClassifier.confirmed_public_browser_form(
                """
                <form>
                  <input name="center" value="41">
                  <select name="service">
                    <option value="4">Confirmed service</option>
                  </select>
                  <select name="date"><option value="">Select</option></select>
                </form>
                """,
                service_center_id="41",
                service_id="4",
            )
        )

    def test_browser_form_guard_rejects_wrong_centre(self) -> None:
        self.assertFalse(
            LandingPageClassifier.confirmed_public_browser_form(
                """
                <form>
                  <input name="center" value="99">
                  <select name="service"><option value="4">Service</option></select>
                  <select name="date"></select>
                </form>
                """,
                service_center_id="41",
                service_id="4",
            )
        )

    def test_public_browser_identifiers_require_one_service(self) -> None:
        html = """
        <form x-data='qlogicFormTotoro({"center": "TEST_CENTRE"})'>
          <select name="service">
            <option value="">Select</option>
            <option value="TEST_SERVICE">Confirmed service</option>
          </select>
          <select name="date"></select>
        </form>
        """
        self.assertEqual(
            LandingPageClassifier.public_browser_form_identifiers(html),
            ("TEST_CENTRE", "TEST_SERVICE"),
        )

    def test_public_browser_identifiers_reject_ambiguous_services(self) -> None:
        html = """
        <form x-data='qlogicFormTotoro({"center": "TEST_CENTRE"})'>
          <select name="service">
            <option value="1">First</option>
            <option value="2">Second</option>
          </select>
          <select name="date"></select>
        </form>
        """
        self.assertIsNone(
            LandingPageClassifier.public_browser_form_identifiers(html)
        )

    def test_no_slots_marker_wins_over_nonblocking_captcha_asset(self) -> None:
        result = LandingPageClassifier().classify(
            200,
            """
            <main>Наразі всі місця зайняті</main>
            <script src="https://js.hcaptcha.com/1/api.js"></script>
            """,
        )
        self.assertEqual(result.state, LandingState.NO_SLOTS)

    def test_explicit_security_challenge_is_blocked(self) -> None:
        result = LandingPageClassifier().classify(
            200,
            """
            <main>Триває перевірка безпеки</main>
            <form id="challenge-form"></form>
            """,
        )
        self.assertEqual(result.state, LandingState.BLOCKED)
        self.assertIn(EvidenceCode.CHALLENGE_MARKER, result.evidence)

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

    def test_madrid_days_classifier_accepts_only_confirmed_schema(self) -> None:
        result = ConfirmedDaysClassifier().classify(
            200,
            {
                "days": [
                    {
                        "datePart": "2026-08-03",
                        "date": "03.08.2026",
                        "isAllowed": True,
                    },
                    {
                        "datePart": "2026-08-04",
                        "date": "04.08.2026",
                        "isAllowed": False,
                    },
                ]
            },
        )
        self.assertTrue(result.recognized)
        self.assertEqual(result.dates, ("2026-08-03",))
        self.assertIn(EvidenceCode.AVAILABLE_DATES_FOUND, result.evidence)

    def test_madrid_days_classifier_fails_closed(self) -> None:
        result = ConfirmedDaysClassifier().classify(
            200,
            {"days": [{"datePart": "2026-08-03", "isAllowed": True}]},
        )
        self.assertFalse(result.recognized)
        self.assertIn(
            EvidenceCode.DAYS_PAYLOAD_UNRECOGNIZED, result.evidence
        )

    def test_madrid_times_classifier_accepts_only_confirmed_schema(self) -> None:
        result = ConfirmedTimesClassifier().classify(
            200,
            {
                "timeSlots": [
                    {
                        "startTime": "12:40:00",
                        "slot": "12:40 — 1 вільний слот",
                        "isAllowed": True,
                    },
                    {
                        "startTime": "13:00:00",
                        "slot": "13:00 — unavailable",
                        "isAllowed": False,
                    },
                ]
            },
        )
        self.assertTrue(result.recognized)
        self.assertEqual(result.times, ("12:40:00",))
        self.assertIn(EvidenceCode.AVAILABLE_TIMES_FOUND, result.evidence)

    def test_madrid_times_classifier_fails_closed(self) -> None:
        result = ConfirmedTimesClassifier().classify(
            200,
            {"timeSlots": [{"startTime": "12:40:00", "isAllowed": True}]},
        )
        self.assertFalse(result.recognized)
        self.assertIn(
            EvidenceCode.TIMES_PAYLOAD_UNRECOGNIZED, result.evidence
        )


if __name__ == "__main__":
    unittest.main()
