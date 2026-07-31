"""Experimental passive Playwright transport for confirmed public discovery.

The transport performs one normal persistent-context navigation, changes only
the confirmed public service/date selectors, and stops after TIMES. It never
touches identity fields, CAPTCHA, continuation, or booking controls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import (
    Page,
    Request,
    Response,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from diagnostics.domain import RequestTraceEntry
from provider_protocol import (
    ConfirmedDaysClassifier,
    ConfirmedTimesClassifier,
    DiscoveryStage,
    LandingPageClassifier,
    LandingState,
)


@dataclass(frozen=True, slots=True)
class BrowserDiscoveryResult:
    state: str
    page_hash: str
    message: str
    evidence: tuple[str, ...]
    discovery_stage: str
    http_status: int | None
    request_trace: tuple[RequestTraceEntry, ...]
    available_dates_count: int | None = None
    available_time_slots_count: int | None = None
    earliest_available_time: str | None = None
    latest_available_time: str | None = None


class PlaywrightDiscoveryTransport:
    """Visible, persistent, non-booking browser transport."""

    def __init__(
        self,
        *,
        city: str,
        queue_url: str,
        service_center_id: str | None,
        service_id: str | None,
        profile_dir: Path,
        timeout_ms: int = 60_000,
        headless: bool = False,
    ) -> None:
        self.city = city
        self.queue_url = queue_url
        self.service_center_id = service_center_id
        self.service_id = service_id
        self.profile_dir = profile_dir
        self.timeout_ms = timeout_ms
        self.headless = headless
        self.landing_classifier = LandingPageClassifier()

    def discover(self) -> BrowserDiscoveryResult:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    str(self.profile_dir),
                    headless=self.headless,
                    locale="uk-UA",
                    viewport={"width": 1440, "height": 1000},
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    return self._discover_page(page)
                finally:
                    context.close()
        except PlaywrightTimeoutError:
            return self._failure(
                "UNKNOWN",
                "Playwright public discovery timed out without retry.",
                "PLAYWRIGHT_TIMEOUT",
            )
        except Exception as error:
            logging.exception("Playwright discovery transport failed.")
            return self._failure(
                "UNKNOWN",
                f"Playwright public discovery failed: {type(error).__name__}.",
                "PLAYWRIGHT_ERROR",
            )

    def _discover_page(self, page: Page) -> BrowserDiscoveryResult:
        started = time.perf_counter()
        document_statuses: list[int] = []
        page.on(
            "response",
            lambda response: document_statuses.append(response.status)
            if (
                response.request.resource_type == "document"
                and response.url.startswith(self.queue_url)
            )
            else None,
        )
        navigation = page.goto(
            self.queue_url,
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )
        page.wait_for_timeout(
            max(0, int(os.getenv("PLAYWRIGHT_DISCOVERY_SETTLE_MS", "5000")))
        )
        html = page.content()
        status = (
            document_statuses[-1]
            if document_statuses
            else navigation.status if navigation is not None else None
        )
        landing_ms = round((time.perf_counter() - started) * 1000)
        page_hash = hashlib.sha256(
            self._normalized_body_text(page).encode("utf-8")
        ).hexdigest()
        traces = [
            RequestTraceEntry(
                method="GET",
                operation="landing",
                status_code=status,
                duration_ms=landing_ms,
                response_bytes=len(html.encode("utf-8")),
                transport="playwright",
            )
        ]
        landing = self.landing_classifier.classify(status or 0, html)
        logging.info("Playwright reached LANDING")
        if landing.state is LandingState.NO_SLOTS:
            return BrowserDiscoveryResult(
                "NO_SLOTS",
                page_hash,
                "Playwright landing contains the confirmed no-slots marker.",
                tuple(item.value for item in landing.evidence),
                DiscoveryStage.LANDING,
                status,
                tuple(traces),
                available_dates_count=0,
                available_time_slots_count=0,
            )
        if landing.state is LandingState.BLOCKED:
            return BrowserDiscoveryResult(
                "BLOCKED",
                page_hash,
                "Playwright encountered a browser challenge and stopped.",
                tuple(item.value for item in landing.evidence),
                DiscoveryStage.LANDING,
                status,
                tuple(traces),
            )
        identifiers = (
            (self.service_center_id, self.service_id)
            if self.service_center_id and self.service_id
            else self.landing_classifier.public_browser_form_identifiers(html)
        )
        if identifiers is None:
            self._log_safe_structure(page, landing.state.value)
            return self._unknown_landing(page_hash, status, traces)
        service_center_id, service_id = identifiers
        browser_form_confirmed = (
            self.landing_classifier.confirmed_public_browser_form(
                html,
                service_center_id=service_center_id,
                service_id=service_id,
            )
        )
        if (
            landing.state is not LandingState.DISCOVERY_READY
            and not browser_form_confirmed
        ):
            self._log_safe_structure(page, landing.state.value)
            return self._unknown_landing(page_hash, status, traces)

        service_selector = 'select[name="service"]'
        if page.locator(service_selector).count() != 1:
            return self._unknown_landing(page_hash, status, traces)
        service = page.locator(service_selector)
        current_service = service.input_value()
        if current_service == service_id:
            placeholder = service.locator('option[value=""]')
            if placeholder.count():
                service.select_option(value="")

        days_started = time.perf_counter()
        with page.expect_response(
            lambda response: self._is_operation(response.request, "days"),
            timeout=self.timeout_ms,
        ) as days_info:
            service.select_option(value=service_id)
        days_response = days_info.value
        days_payload = self._response_json(days_response)
        days_ms = round((time.perf_counter() - days_started) * 1000)
        traces.append(
            self._trace(days_response, "days", days_ms, days_payload)
        )
        days = ConfirmedDaysClassifier().classify(
            days_response.status, days_payload
        )
        logging.info("Playwright reached DAYS")
        if not days.recognized:
            return BrowserDiscoveryResult(
                "UNKNOWN",
                page_hash,
                "Playwright days response did not match the confirmed schema.",
                tuple(item.value for item in days.evidence),
                DiscoveryStage.DAYS,
                status,
                tuple(traces),
            )
        if not days.dates:
            return BrowserDiscoveryResult(
                "NO_SLOTS",
                page_hash,
                "Playwright found no publicly available dates.",
                tuple(item.value for item in days.evidence),
                DiscoveryStage.DAYS,
                status,
                tuple(traces),
                available_dates_count=0,
                available_time_slots_count=0,
            )

        date_selector = 'select[name="date"], select[name="Date"]'
        if page.locator(date_selector).count() != 1:
            return BrowserDiscoveryResult(
                "UNKNOWN",
                page_hash,
                "Playwright did not find the confirmed public date selector.",
                ("TIMES_PAYLOAD_UNRECOGNIZED",),
                DiscoveryStage.TIMES,
                status,
                tuple(traces),
                available_dates_count=len(days.dates),
            )

        all_times: list[str] = []
        evidence = [item.value for item in days.evidence]
        date_select = page.locator(date_selector)
        for available_date in days.dates:
            times_started = time.perf_counter()
            with page.expect_response(
                lambda response: self._is_operation(
                    response.request, "times"
                ),
                timeout=self.timeout_ms,
            ) as times_info:
                date_select.select_option(value=available_date)
            times_response = times_info.value
            times_payload = self._response_json(times_response)
            times_ms = round((time.perf_counter() - times_started) * 1000)
            traces.append(
                self._trace(
                    times_response, "times", times_ms, times_payload
                )
            )
            times = ConfirmedTimesClassifier().classify(
                times_response.status, times_payload
            )
            if not times.recognized:
                return BrowserDiscoveryResult(
                    "UNKNOWN",
                    page_hash,
                    "Playwright times response did not match the confirmed schema.",
                    tuple(item.value for item in times.evidence),
                    DiscoveryStage.TIMES,
                    status,
                    tuple(traces),
                    available_dates_count=len(days.dates),
                )
            evidence.extend(item.value for item in times.evidence)
            all_times.extend(times.times)

        logging.info("Playwright reached TIMES")
        logging.info("Stopping at confirmed public discovery boundary.")
        earliest = min(all_times) if all_times else None
        latest = max(all_times) if all_times else None
        return BrowserDiscoveryResult(
            "SLOTS_AVAILABLE" if all_times else "POSSIBLE_SLOTS",
            page_hash,
            (
                f"Available dates: {len(days.dates)}; "
                f"available time slots: {len(all_times)}; "
                f"earliest: {earliest or 'none'}; latest: {latest or 'none'}."
            ),
            tuple(dict.fromkeys(evidence)),
            DiscoveryStage.TIMES,
            status,
            tuple(traces),
            available_dates_count=len(days.dates),
            available_time_slots_count=len(all_times),
            earliest_available_time=earliest,
            latest_available_time=latest,
        )

    @staticmethod
    def _normalized_body_text(page: Page) -> str:
        return " ".join(page.locator("body").inner_text().split())

    def _log_safe_structure(self, page: Page, reason: str) -> None:
        """Log selector counts only; never log DOM, tokens, or payloads."""
        logging.info(
            "Playwright LANDING structure: reason=%s title=%r forms=%s "
            "service_selects=%s confirmed_service_options=%s "
            "date_selects=%s challenge_forms=%s challenge_iframes=%s",
            reason,
            page.title(),
            page.locator("form").count(),
            page.locator('select[name="service"]').count(),
            page.locator(
                f'select[name="service"] option[value="{self.service_id or ""}"]'
            ).count(),
            page.locator(
                'select[name="date"], select[name="Date"]'
            ).count(),
            page.locator("#challenge-form").count(),
            page.locator(
                'iframe[src*="challenge"], iframe[src*="captcha"]'
            ).count(),
        )

    @staticmethod
    def _is_operation(request: Request, operation: str) -> bool:
        if request.method != "POST":
            return False
        body = request.post_data or ""
        return (
            f'name="form"\r\n\r\n{operation}' in body
            or f"form={operation}" in body
        )

    @staticmethod
    def _response_json(response: Response) -> object:
        try:
            return response.json()
        except Exception:
            return None

    @staticmethod
    def _trace(
        response: Response,
        operation: str,
        duration_ms: int,
        payload: object,
    ) -> RequestTraceEntry:
        size = len(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ) if payload is not None else 0
        return RequestTraceEntry(
            method="POST",
            operation=operation,
            status_code=response.status,
            duration_ms=duration_ms,
            response_bytes=size,
            transport="playwright",
        )

    def _unknown_landing(
        self,
        page_hash: str,
        status: int | None,
        traces: list[RequestTraceEntry],
    ) -> BrowserDiscoveryResult:
        return BrowserDiscoveryResult(
            "UNKNOWN",
            page_hash,
            "Playwright landing did not match the confirmed public form.",
            ("UNRECOGNIZED_HTML",),
            DiscoveryStage.LANDING,
            status,
            tuple(traces),
        )

    @staticmethod
    def _failure(
        state: str,
        message: str,
        evidence: str,
    ) -> BrowserDiscoveryResult:
        return BrowserDiscoveryResult(
            state,
            "",
            message,
            (evidence,),
            DiscoveryStage.LANDING,
            None,
            (),
        )
