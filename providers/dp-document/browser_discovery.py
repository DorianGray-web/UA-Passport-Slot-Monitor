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
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import (
    Page,
    Request,
    Response,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from diagnostics.domain import RequestTraceEntry
from provider_protocol import (
    CandidateQueueForm,
    ConfirmedDaysClassifier,
    ConfirmedTimesClassifier,
    DiscoveryStage,
    EvidenceCode,
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
    candidate_form: CandidateQueueForm | None = None


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
        browser_channel: str | None = None,
    ) -> None:
        self.city = city
        self.queue_url = queue_url
        self.service_center_id = service_center_id
        self.service_id = service_id
        self.profile_dir = profile_dir
        self.timeout_ms = timeout_ms
        self.headless = headless
        self.browser_channel = browser_channel
        self.landing_classifier = LandingPageClassifier()

    def discover(self) -> BrowserDiscoveryResult:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as playwright:
                browser_launch_started = time.perf_counter()
                context = playwright.chromium.launch_persistent_context(
                    str(self.profile_dir),
                    headless=self.headless,
                    channel=self.browser_channel,
                    locale="uk-UA",
                    viewport={"width": 1440, "height": 1000},
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    browser_version = (
                        context.browser.version
                        if context.browser is not None
                        else "unknown"
                    )
                    return self._discover_page(
                        page,
                        browser_launch_started=browser_launch_started,
                        browser_version=browser_version,
                    )
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

    def probe_landing(self) -> BrowserDiscoveryResult:
        """Observe public landing structure without selecting any option."""
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    str(self.profile_dir),
                    headless=self.headless,
                    channel=self.browser_channel,
                    locale="uk-UA",
                    viewport={"width": 1440, "height": 1000},
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    return self._probe_landing_page(page)
                finally:
                    context.close()
        except PlaywrightTimeoutError:
            return self._candidate_failure(
                "Playwright landing evidence probe timed out without retry.",
                "PLAYWRIGHT_TIMEOUT",
            )
        except Exception as error:
            logging.exception("Playwright landing evidence probe failed.")
            return self._candidate_failure(
                f"Playwright landing evidence probe failed: {type(error).__name__}.",
                "PLAYWRIGHT_ERROR",
            )

    def _probe_landing_page(self, page: Page) -> BrowserDiscoveryResult:
        started = time.perf_counter()
        navigation = page.goto(
            self.queue_url,
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )
        page.wait_for_timeout(
            max(0, int(os.getenv("PLAYWRIGHT_DISCOVERY_SETTLE_MS", "5000")))
        )
        html = page.content()
        status = navigation.status if navigation is not None else None
        duration_ms = round((time.perf_counter() - started) * 1000)
        page_hash = hashlib.sha256(
            self._normalized_body_text(page).encode("utf-8")
        ).hexdigest()
        trace = RequestTraceEntry(
            method="GET",
            operation="landing",
            status_code=status,
            duration_ms=duration_ms,
            response_bytes=len(html.encode("utf-8")),
            transport="playwright",
        )
        landing = self.landing_classifier.classify(status or 0, html)
        candidate = self.landing_classifier.candidate_public_form(html)
        logging.info("Playwright candidate probe reached LANDING")
        if candidate is not None:
            logging.info(
                "Candidate landing form detected: service_center=%s "
                "option_count=%s date_selector=%s time_selector=%s",
                candidate.service_center_id or "unknown",
                len(candidate.options),
                candidate.date_selector_found,
                candidate.time_selector_found,
            )
            logging.info("Stopping candidate probe at LANDING boundary.")
            return BrowserDiscoveryResult(
                "UNKNOWN",
                page_hash,
                "Candidate queue form detected; governance review required.",
                (
                    EvidenceCode.CANDIDATE_EVIDENCE_PROBE.value,
                    *(item.value for item in landing.evidence),
                ),
                DiscoveryStage.LANDING,
                status,
                (trace,),
                candidate_form=candidate,
            )
        state = (
            "NO_SLOTS"
            if landing.state is LandingState.NO_SLOTS
            else "BLOCKED"
            if landing.state is LandingState.BLOCKED
            else "UNKNOWN"
        )
        return BrowserDiscoveryResult(
            state,
            page_hash,
            "Playwright landing probe found no candidate queue form.",
            (
                EvidenceCode.CANDIDATE_EVIDENCE_PROBE.value,
                *(item.value for item in landing.evidence),
            ),
            DiscoveryStage.LANDING,
            status,
            (trace,),
        )

    @staticmethod
    def _sanitized_navigation_url(url: str) -> str:
        parsed = urlsplit(url)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

    def _launch_config_hash(self, browser_version: str) -> str:
        controlled_config = {
            "browser_channel": self.browser_channel or "bundled",
            "browser_version": browser_version,
            "headless": self.headless,
            "locale": "uk-UA",
            "persistent_context": True,
            "viewport": {"height": 1000, "width": 1440},
        }
        serialized = json.dumps(
            controlled_config,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _main_frame_redirect_chain(navigation: Response | None) -> str:
        if navigation is None:
            return "none"
        requests: list[Request] = []
        request: Request | None = navigation.request
        while request is not None:
            requests.append(request)
            request = request.redirected_from
        requests.reverse()
        return " -> ".join(
            PlaywrightDiscoveryTransport._sanitized_navigation_url(item.url)
            for item in requests
        )

    @staticmethod
    def _form_structure_complete(evidence: tuple[EvidenceCode, ...]) -> bool:
        required = {
            EvidenceCode.QUEUE_FORM_FOUND,
            EvidenceCode.SERVICE_SELECTOR_FOUND,
            EvidenceCode.DATE_SELECTOR_FOUND,
            EvidenceCode.TIME_SELECTOR_FOUND,
        }
        return required.issubset(set(evidence))

    def _challenge_source(
        self,
        *,
        html: str,
        final_url: str,
        iframe_urls: tuple[str, ...],
        challenge_form_found: bool,
    ) -> tuple[str, EvidenceCode | None]:
        lowered = html.lower()
        sources: set[str] = set()
        if any(
            marker in lowered
            for marker in self.landing_classifier.BLOCKING_CHALLENGE_MARKERS
            if marker != 'id="challenge-form"'
        ):
            sources.add("html_marker")
        if challenge_form_found:
            sources.add("challenge_form")
        if any(
            marker in final_url.lower()
            for marker in ("challenge", "captcha", "turnstile", "cdn-cgi")
        ):
            sources.add("main_frame_url")
        if any(
            marker in url.lower()
            for url in iframe_urls
            for marker in ("challenge", "captcha", "turnstile", "hcaptcha")
        ):
            sources.add("iframe_document")
        if not sources:
            return "none", None
        if len(sources) > 1:
            return "mixed", EvidenceCode.CHALLENGE_SOURCE_MIXED
        source = next(iter(sources))
        evidence = {
            "html_marker": EvidenceCode.CHALLENGE_SOURCE_HTML_MARKER,
            "challenge_form": EvidenceCode.CHALLENGE_SOURCE_CHALLENGE_FORM,
            "main_frame_url": EvidenceCode.CHALLENGE_SOURCE_MAIN_FRAME_URL,
            "iframe_document": EvidenceCode.CHALLENGE_SOURCE_IFRAME_DOCUMENT,
        }[source]
        return source, evidence

    def _discover_page(
        self,
        page: Page,
        *,
        browser_launch_started: float | None = None,
        browser_version: str = "unknown",
    ) -> BrowserDiscoveryResult:
        started = time.perf_counter()
        launch_started = browser_launch_started or started
        navigation = page.goto(
            self.queue_url,
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )
        navigation_response_ms = round(
            (time.perf_counter() - launch_started) * 1000
        )
        page.wait_for_timeout(
            max(0, int(os.getenv("PLAYWRIGHT_DISCOVERY_SETTLE_MS", "5000")))
        )
        html = page.content()
        status = navigation.status if navigation is not None else None
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
        redirect_chain = self._main_frame_redirect_chain(navigation)
        iframe_urls = tuple(
            frame.url for frame in page.frames if frame is not page.main_frame
        )
        challenge_form_found = page.locator("#challenge-form").count() > 0
        challenge_source, challenge_source_evidence = self._challenge_source(
            html=html,
            final_url=page.url,
            iframe_urls=iframe_urls,
            challenge_form_found=challenge_form_found,
        )
        challenge_present = challenge_source != "none"
        form_structure_complete = self._form_structure_complete(landing.evidence)
        main_frame_challenge_url = any(
            marker in page.url.lower()
            for marker in ("challenge", "captcha", "turnstile", "cdn-cgi")
        )
        active_gate = challenge_form_found or main_frame_challenge_url
        challenge_blocks_discovery = "true" if active_gate else "unknown"
        challenge_interaction_required = "true" if active_gate else "unknown"
        challenge_widget_visible = any(
            locator.is_visible()
            for selector in (
                "#challenge-form",
                ".h-captcha",
                '[class*="turnstile"]',
                'iframe[src*="captcha"]',
                'iframe[src*="challenge"]',
                'iframe[src*="turnstile"]',
            )
            for locator in [page.locator(selector).first]
            if locator.count() > 0
        )
        logging.info(
            "Playwright first navigation: initial_url=%s final_url=%s "
            "main_document_status=%s redirect_chain=%s "
            "browser_start_to_navigation_response_ms=%s "
            "redirect_chain_telemetry_valid=true challenge_present=%s "
            "challenge_source=%s challenge_blocks_discovery=%s "
            "challenge_interaction_required=%s form_structure_complete=%s "
            "challenge_widget_visible=%s days_request_sent=false "
            "times_request_sent=false browser_channel=%s browser_version=%s "
            "launch_config_hash=%s launch_config_scope=application-controlled",
            self._sanitized_navigation_url(self.queue_url),
            self._sanitized_navigation_url(page.url),
            status if status is not None else "none",
            redirect_chain,
            navigation_response_ms,
            str(challenge_present).lower(),
            challenge_source,
            challenge_blocks_discovery,
            challenge_interaction_required,
            str(form_structure_complete).lower(),
            str(challenge_widget_visible).lower(),
            self.browser_channel or "bundled",
            browser_version,
            self._launch_config_hash(browser_version),
        )
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
            refined_evidence = list(landing.evidence)
            if challenge_source_evidence is not None:
                refined_evidence.append(challenge_source_evidence)
            if form_structure_complete:
                refined_evidence.append(EvidenceCode.FORM_STRUCTURE_COMPLETE)
            if active_gate:
                refined_evidence.extend(
                    (
                        EvidenceCode.ACTIVE_CHALLENGE_GATE,
                        EvidenceCode.CHALLENGE_INTERACTION_REQUIRED,
                    )
                )
            elif challenge_present:
                refined_evidence.extend(
                    (
                        EvidenceCode.EMBEDDED_CHALLENGE_ASSET_PRESENT,
                        EvidenceCode.CHALLENGE_EFFECT_UNDETERMINED,
                    )
                )
            return BrowserDiscoveryResult(
                "BLOCKED",
                page_hash,
                "Playwright encountered a browser challenge and stopped.",
                tuple(dict.fromkeys(item.value for item in refined_evidence)),
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

    @staticmethod
    def _candidate_failure(
        message: str,
        evidence: str,
    ) -> BrowserDiscoveryResult:
        return BrowserDiscoveryResult(
            "UNKNOWN",
            "",
            message,
            (EvidenceCode.CANDIDATE_EVIDENCE_PROBE.value, evidence),
            DiscoveryStage.LANDING,
            None,
            (),
        )
