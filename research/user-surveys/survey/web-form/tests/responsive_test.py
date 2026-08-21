import functools
import json
import re
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
FORM_PATH = "/research/user-surveys/survey/web-form/index.html"
VIEWPORTS = (320, 360, 390, 430, 768)
LOCALES = ("en", "uk", "ru")
STEP_NAMES = ("introduction", "situation", "centres", "problems", "notifications", "testing")


class ResponsiveSurveyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(SimpleHTTPRequestHandler, directory=REPOSITORY_ROOT)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}{FORM_PATH}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)

    def assert_no_horizontal_overflow(self, page, locale, width, step):
        dimensions = page.evaluate(
            """() => ({
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
            })"""
        )
        self.assertLessEqual(
            dimensions["scrollWidth"],
            dimensions["clientWidth"],
            f"horizontal overflow at locale={locale}, width={width}, step={step}: {dimensions}",
        )

    def continue_button(self, page, locale):
        labels = {"en": "Continue", "uk": "Продовжити", "ru": "Продолжить"}
        return page.get_by_role("button", name=labels[locale])

    def test_no_horizontal_overflow_across_locales_viewports_and_steps(self):
        for locale in LOCALES:
            for width in VIEWPORTS:
                page = self.browser.new_page(viewport={"width": width, "height": 900})
                try:
                    page.goto(f"{self.base_url}?responsive-test={locale}-{width}")
                    page.wait_for_selector('input[name="consent_research"]')
                    if locale != "en":
                        page.select_option("#locale-picker", locale)
                    page.wait_for_timeout(50)
                    self.assert_no_horizontal_overflow(page, locale, width, STEP_NAMES[0])

                    page.locator('input[name="consent_research"]').check()
                    self.continue_button(page, locale).click()
                    page.locator('input[name="residence_region_id"][value="eu"]').check()
                    page.locator('input[name="service_id"][value="id_card"]').check()
                    page.locator('input[name="slot_search_experience"][value="not_started"]').check()
                    page.locator('input[name="check_frequency"][value="daily"]').check()
                    self.assert_no_horizontal_overflow(page, locale, width, STEP_NAMES[1])

                    self.continue_button(page, locale).click()
                    self.assert_no_horizontal_overflow(page, locale, width, STEP_NAMES[2])
                    page.locator('input[name="centre_ids"][value="munich"]').check()

                    self.continue_button(page, locale).click()
                    self.assert_no_horizontal_overflow(page, locale, width, STEP_NAMES[3])
                    page.locator('input[name="problem_category_ids"][value="none"]').check()

                    self.continue_button(page, locale).click()
                    self.assert_no_horizontal_overflow(page, locale, width, STEP_NAMES[4])
                    page.locator('input[name="notification_channel_ids"][value="none"]').check()
                    page.locator('input[name="primary_notification_channel_id"][value="none"]').check()
                    page.locator('input[name="manual_captcha_attitude"][value="not_sure"]').check()

                    self.continue_button(page, locale).click()
                    self.assert_no_horizontal_overflow(page, locale, width, STEP_NAMES[5])
                finally:
                    page.close()

    def test_one_submit_produces_one_normalized_debug_payload(self):
        app_source = (Path(__file__).resolve().parents[1] / "js" / "app.js").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"form\.addEventListener\(['\"]submit['\"]", app_source)), 1)
        self.assertEqual(len(re.findall(r"submitSurvey\(payload\)", app_source)), 1)

        page = self.browser.new_page(viewport={"width": 390, "height": 900})
        try:
            page.goto(f"{self.base_url}?debug=1&submit-test=1")
            page.wait_for_selector('input[name="consent_research"]')
            page.locator('input[name="consent_research"]').check()
            self.continue_button(page, "en").click()
            page.locator('input[name="residence_region_id"][value="eu"]').check()
            page.locator('input[name="service_id"][value="other"]').check()
            page.locator('input[name="other_service_text"]').fill("  Some  text  ")
            page.locator('input[name="slot_search_experience"][value="not_started"]').check()
            page.locator('input[name="check_frequency"][value="daily"]').check()
            self.continue_button(page, "en").click()
            self.continue_button(page, "en").click()
            page.locator('input[name="centre_ids"][value="munich"]').check()
            self.continue_button(page, "en").click()
            page.locator('input[name="problem_category_ids"][value="none"]').check()
            self.continue_button(page, "en").click()
            page.locator('input[name="notification_channel_ids"][value="none"]').check()
            page.locator('input[name="primary_notification_channel_id"][value="none"]').check()
            page.locator('input[name="manual_captcha_attitude"][value="not_sure"]').check()
            self.continue_button(page, "en").click()
            page.locator('input[name="early_testing_interest"][value="maybe"]').check()
            page.locator('textarea[name="additional_context"]').fill("   ")
            page.get_by_role("button", name="Submit survey").click()
            page.wait_for_selector("#debug-payload:not(:empty)")
            payload = json.loads(page.locator("#debug-payload").inner_text())
            self.assertEqual(payload["answers"]["other_service_text"], "Some  text")
            self.assertIsNone(payload["answers"]["additional_context"])
            self.assertEqual(page.locator("#form-status").inner_text(), "Demo mode: your response was validated locally and was not sent to a server.")
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
