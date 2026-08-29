from __future__ import annotations

import functools
import json
import shutil
import subprocess
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


SPIKE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
SCHEMA_PATH = REPOSITORY_ROOT / "research/user-surveys/shared/schemas/survey-response.schema.json"
FIXTURE_PATH = SPIKE_ROOT / "fixtures/valid-survey-response.json"
HARNESS_PATH = "/research/user-surveys/survey/spikes/apps-script-contract-validation/harness/index.html"


class ContractFixtureTest(unittest.TestCase):
    def schema_valid(self, payload: dict) -> bool:
        pwsh = shutil.which("pwsh")
        self.assertIsNotNone(pwsh, "PowerShell 7 is required for canonical Draft 2020-12 validation")
        script = "$json = [Console]::In.ReadToEnd(); if ($json | Test-Json -SchemaFile $args[0] -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
        result = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-CommandWithArgs", script, str(SCHEMA_PATH)],
            input=json.dumps(payload), text=True, capture_output=True, check=False,
        )
        return result.returncode == 0

    def setUp(self):
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_known_good_and_controlled_schema_mutations(self):
        self.assertTrue(self.schema_valid(self.fixture))
        missing = json.loads(json.dumps(self.fixture))
        del missing["answers"]["appointment_urgency"]
        self.assertFalse(self.schema_valid(missing))
        invalid_uuid = json.loads(json.dumps(self.fixture))
        invalid_uuid["response_id"] = "not-a-uuid"
        self.assertFalse(self.schema_valid(invalid_uuid))
        invalid_taxonomy = json.loads(json.dumps(self.fixture))
        invalid_taxonomy["answers"]["centre_ids"] = ["nonexistent_centre"]
        self.assertFalse(self.schema_valid(invalid_taxonomy))
        wrong_type = json.loads(json.dumps(self.fixture))
        wrong_type["answers"]["problem_category_ids"] = "none"
        self.assertFalse(self.schema_valid(wrong_type))

    def test_generated_snapshot_is_current(self):
        subprocess.run(
            [shutil.which("python") or "python", str(SPIKE_ROOT / "tools/build_contract_snapshot.py"), "--check"],
            cwd=REPOSITORY_ROOT, check=True,
        )


class HarnessSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(SimpleHTTPRequestHandler, directory=REPOSITORY_ROOT)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel="chrome", headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_harness_loads_without_adapter_request_or_persistent_state(self):
        page = self.browser.new_page(viewport={"width": 320, "height": 900})
        console_errors = []
        adapter_requests = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: adapter_requests.append(request.url) if "script.google.com" in request.url else None)
        try:
            page.goto(f"http://127.0.0.1:{self.server.server_port}{HARNESS_PATH}")
            page.wait_for_function("document.querySelector('#fixture-status').textContent.includes('ready')")
            self.assertEqual(page.locator("[data-case]").count(), 10)
            self.assertFalse(page.locator('[data-case="1"]').is_disabled())
            self.assertTrue(page.locator('[data-case="2"]').is_disabled())
            self.assertTrue(page.locator('[data-case="10"]').is_disabled())
            self.assertEqual(adapter_requests, [])
            self.assertEqual(console_errors, [])
            self.assertEqual(page.evaluate("localStorage.length"), 0)
            self.assertEqual(page.evaluate("sessionStorage.length"), 0)
            self.assertEqual(page.evaluate("indexedDB.databases().then(items => items.length)"), 0)
            self.assertEqual(page.context.cookies(), [])
            dimensions = page.evaluate("({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth })")
            self.assertLessEqual(dimensions["scrollWidth"], dimensions["clientWidth"])

            test_host = "https://" + "script.google.com"
            page.route(
                test_host + "/**",
                lambda route: route.fulfill(
                    status=200,
                    headers={"access-control-allow-origin": "*", "content-type": "application/json"},
                    body=json.dumps({"spike_version": "3.0.0", "outcome": "ACCEPTED"}),
                ),
            )
            page.locator("#endpoint").fill(test_host + "/macros/s/TEST_ONLY/exec")
            page.locator('[data-case="1"]').click()
            page.wait_for_function("document.querySelector('[data-case-card=\"1\"] .status').textContent === 'PASS'")
            self.assertFalse(page.locator('[data-case="2"]').is_disabled())
            self.assertFalse(page.locator('[data-case="10"]').is_disabled())
            self.assertEqual(page.evaluate("localStorage.length + sessionStorage.length"), 0)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
