from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from diagnostics.domain import RequestTraceEntry, make_run_id
from diagnostics.event_store import SQLiteEventStore
from diagnostics.monitoring import ObservationService
from browser_discovery import PlaywrightDiscoveryTransport
from candidate_evidence import CandidateEvidenceStore
from dp_document_http import DPDocumentHTTPMonitorProvider
from monitor_metadata import utc_timestamp
from provider_boundaries import DaysRequest, TimesRequest
from provider_protocol import (
    DiscoveryStage,
    LandingPageClassifier,
    LandingState,
    ConfirmedDaysClassifier,
    ConfirmedTimesClassifier,
    TransitionGuard,
)


MIN_INTERVAL_SECONDS = 7 * 60
MAX_INTERVAL_SECONDS = 12 * 60
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_BLOCKED_COOLDOWN_SECONDS = 60 * 60
DEFAULT_DIAGNOSTIC_EVENTS = {
    "BLOCKED",
    "UNKNOWN",
    "HTML_STRUCTURE_CHANGED",
    "QUEUE_SECTION_CHANGED",
}
CONFIRMED_PUBLIC_DISCOVERY_PROFILES = {
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


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    city: str
    provider: str
    queue_url: str
    env_prefix: str
    base_dir: Path
    project_dir: Path | None = None
    public_discovery_profile: str | None = None
    service_center_id: str | None = None
    service_id: str | None = None
    csrf_value: str | None = None
    candidate_evidence_probe: bool = False

    @property
    def slug(self) -> str:
        return self.city.lower()

    def env_path(self, suffix: str, default: Path) -> Path:
        return Path(os.getenv(f"{self.env_prefix}_{suffix}", default))


@dataclass(slots=True)
class QueueState:
    status: str
    checked_at: str
    page_hash: str
    message: str
    source: str
    evidence: tuple[str, ...] = ()
    discovery_stage: str = DiscoveryStage.LANDING
    available_dates_count: int | None = None
    available_time_slots_count: int | None = None
    earliest_available_time: str | None = None
    latest_available_time: str | None = None
    request_trace: tuple[RequestTraceEntry, ...] = ()


class CityMonitor:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        project_dir = config.project_dir or PROJECT_DIR
        self.data_dir = config.env_path("DATA_DIR", config.base_dir / "data")
        self.log_dir = config.env_path("LOG_DIR", project_dir / "logs")
        self.metadata_dir = config.env_path(
            "METADATA_DIR", project_dir / "metadata"
        )
        self.state_file = self.data_dir / f"{config.slug}_state.json"
        self.log_file = self.log_dir / f"{config.slug}.log"
        self.metadata_file = self.metadata_dir / f"{config.slug}.jsonl"
        self.observation_store = SQLiteEventStore(
            Path(
                os.getenv(
                    "OBSERVATION_STORE_PATH",
                    project_dir / "data" / "observations.sqlite3",
                )
            )
        )
        self.observation_service = ObservationService(
            self.observation_store,
            run_id=os.getenv("MONITOR_RUN_ID", make_run_id()),
            jsonl_export=self.metadata_file,
        )
        self.landing_classifier = LandingPageClassifier(
            os.getenv(f"{config.env_prefix}_CSRF_FIELD") or None
        )
        self.session = requests.Session()
        self.project_dir = project_dir
        candidate_root = config.env_path(
            "CANDIDATE_EVIDENCE_DIR",
            project_dir
            / "research-output"
            / "candidate-evidence"
            / config.slug,
        )
        self.candidate_evidence = CandidateEvidenceStore(
            candidate_root, config.provider
        )

    def configure_logging(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler(self.log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
            force=True,
        )

    def fetch_page(self) -> tuple[int, str]:
        response = self.session.get(
            self.config.queue_url,
            headers={
                "User-Agent": (
                    "UA-Passport-Slot-Monitor/0.2 "
                    "(research prototype; contact via GitHub)"
                ),
                "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return response.status_code, response.text

    def playwright_fallback_enabled(self) -> bool:
        if (
            self.config.public_discovery_profile
            not in CONFIRMED_PUBLIC_DISCOVERY_PROFILES
        ):
            return False
        value = os.getenv(
            f"{self.config.env_prefix}_PLAYWRIGHT_FALLBACK_ENABLED",
            os.getenv("PLAYWRIGHT_DISCOVERY_FALLBACK_ENABLED", "false"),
        )
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def candidate_probe_enabled(self) -> bool:
        if (
            self.config.public_discovery_profile is not None
            or not self.config.candidate_evidence_probe
        ):
            return False
        value = os.getenv(
            f"{self.config.env_prefix}_CANDIDATE_PROBE_ENABLED",
            os.getenv("CANDIDATE_EVIDENCE_PROBE_ENABLED", "false"),
        )
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def candidate_probe_cooldown_seconds(self) -> int:
        return max(
            0,
            int(os.getenv("CANDIDATE_EVIDENCE_PROBE_COOLDOWN_SECONDS", "21600")),
        )

    def collect_candidate_evidence(
        self,
        *,
        html: str,
        state: QueueState,
        transport: str,
    ) -> bool:
        candidate = self.landing_classifier.candidate_public_form(html)
        if candidate is None:
            return False
        path = self.candidate_evidence.write_candidate(
            observed_at=state.checked_at,
            transport=transport,
            page_hash=state.page_hash,
            candidate=candidate,
        )
        logging.info(
            "Candidate evidence recorded locally: path=%s "
            "service_center=%s option_count=%s",
            path,
            candidate.service_center_id or "unknown",
            len(candidate.options),
        )
        return True

    def run_browser_fallback(
        self,
        http_state: QueueState,
    ) -> tuple[QueueState, int | None]:
        centre = self.config.service_center_id
        service = self.config.service_id
        profile_dir = self.config.env_path(
            "PLAYWRIGHT_PROFILE_DIR",
            self.project_dir / ".browser-data" / self.config.slug,
        )
        headless_value = os.getenv(
            "PLAYWRIGHT_DISCOVERY_HEADLESS", "false"
        )
        transport = PlaywrightDiscoveryTransport(
            city=self.config.city,
            queue_url=self.config.queue_url,
            service_center_id=centre,
            service_id=service,
            profile_dir=profile_dir,
            headless=headless_value.strip().lower()
            in {"1", "true", "yes", "on"},
        )
        result = transport.discover()
        return (
            QueueState(
                result.state,
                utc_timestamp(),
                result.page_hash or http_state.page_hash,
                result.message,
                "playwright",
                result.evidence,
                result.discovery_stage,
                result.available_dates_count,
                result.available_time_slots_count,
                result.earliest_available_time,
                result.latest_available_time,
                (*http_state.request_trace, *result.request_trace),
            ),
            result.http_status,
        )

    def run_browser_candidate_probe(
        self,
        http_state: QueueState,
    ) -> tuple[QueueState, int | None]:
        profile_dir = self.config.env_path(
            "PLAYWRIGHT_PROFILE_DIR",
            self.project_dir / ".browser-data" / self.config.slug,
        )
        headless_value = os.getenv(
            "PLAYWRIGHT_DISCOVERY_HEADLESS", "false"
        )
        transport = PlaywrightDiscoveryTransport(
            city=self.config.city,
            queue_url=self.config.queue_url,
            service_center_id=None,
            service_id=None,
            profile_dir=profile_dir,
            headless=headless_value.strip().lower()
            in {"1", "true", "yes", "on"},
        )
        result = transport.probe_landing()
        state = QueueState(
            result.state,
            utc_timestamp(),
            result.page_hash or http_state.page_hash,
            result.message,
            "playwright",
            result.evidence,
            result.discovery_stage,
            request_trace=(*http_state.request_trace, *result.request_trace),
        )
        if result.candidate_form is not None:
            path = self.candidate_evidence.write_candidate(
                observed_at=state.checked_at,
                transport="playwright",
                page_hash=state.page_hash,
                candidate=result.candidate_form,
            )
            logging.info("Candidate evidence recorded locally: path=%s", path)
        return state, result.http_status

    def _post_public_discovery(
        self,
        *,
        form: str,
        fields: dict[str, str],
    ) -> tuple[int, object, int, int]:
        csrf_fields = set(fields) - {
            "ServiceCenterId",
            "ServiceId",
            "Date",
        }
        if len(csrf_fields) != 1:
            raise ValueError("Public discovery requires one CSRF field.")
        csrf_field = csrf_fields.pop()
        provider = DPDocumentHTTPMonitorProvider(
            provider_id=self.config.provider,
            queue_url=self.config.queue_url,
            csrf_field=csrf_field,
            session=self.session,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        )
        if form == "days":
            result = provider.get_days(
                DaysRequest(
                    fields["ServiceCenterId"],
                    fields["ServiceId"],
                    fields[csrf_field],
                )
            )
        elif form == "times":
            result = provider.get_times(
                TimesRequest(
                    fields["ServiceCenterId"],
                    fields["ServiceId"],
                    fields["Date"],
                    fields[csrf_field],
                )
            )
        else:
            raise ValueError(f"Unsupported public discovery form: {form}")
        return (
            result.status_code,
            result.payload,
            result.duration_ms,
            result.response_bytes,
        )

    def discover_public_availability(
        self,
        *,
        landing_status: int,
        landing_html: str,
        landing_trace: RequestTraceEntry,
    ) -> QueueState:
        """Run a confirmed public protocol profile and stop after TIMES."""
        landing = self.landing_classifier.classify(
            landing_status, landing_html
        )
        base = self.classify_state(landing_status, landing_html)
        base.request_trace = (landing_trace,)
        if (
            self.config.public_discovery_profile
            not in CONFIRMED_PUBLIC_DISCOVERY_PROFILES
        ):
            return base
        if landing.state is not LandingState.DISCOVERY_READY:
            return base

        centre = self.config.service_center_id
        service = self.config.service_id
        if not centre or not service:
            identifiers = self.landing_classifier.public_browser_form_identifiers(
                landing_html
            )
            if identifiers is None:
                base.status = "UNKNOWN"
                base.message = (
                    f"{self.config.city} public form identifiers were not "
                    "unambiguous; discovery stopped."
                )
                return base
            centre, service = identifiers
        csrf_field = (
            self.landing_classifier.confirmed_public_form_csrf_field(
            landing_html,
            service_center_id=str(centre or ""),
            service_id=str(service or ""),
        )
        )
        csrf_value = self.config.csrf_value
        if not all((centre, service, csrf_field, csrf_value)):
            base.status = "UNKNOWN"
            base.message = (
                f"{self.config.city} discovery configuration is incomplete "
                "or does not match the confirmed landing form."
            )
            return base

        common = {
            "ServiceCenterId": str(centre),
            "ServiceId": str(service),
            str(csrf_field): str(csrf_value),
        }
        days_status, days_payload, days_ms, days_bytes = (
            self._post_public_discovery(form="days", fields=common)
        )
        traces = [
            landing_trace,
            RequestTraceEntry(
                method="POST",
                operation="days",
                status_code=days_status,
                duration_ms=days_ms,
                response_bytes=days_bytes,
            ),
        ]
        days = ConfirmedDaysClassifier().classify(days_status, days_payload)
        if not days.recognized:
            return QueueState(
                "UNKNOWN",
                utc_timestamp(),
                base.page_hash,
                f"{self.config.city} days response did not match the "
                "confirmed schema.",
                "http",
                tuple(item.value for item in days.evidence),
                DiscoveryStage.DAYS,
                request_trace=tuple(traces),
            )
        if not TransitionGuard.allows_times(dates=days.dates):
            return QueueState(
                "NO_SLOTS",
                utc_timestamp(),
                base.page_hash,
                f"No publicly available {self.config.city} dates were "
                "returned.",
                "http",
                tuple(item.value for item in days.evidence),
                DiscoveryStage.DAYS,
                available_dates_count=0,
                available_time_slots_count=0,
                request_trace=tuple(traces),
            )

        all_times: list[str] = []
        evidence = [item.value for item in days.evidence]
        for available_date in days.dates:
            times_status, times_payload, times_ms, times_bytes = (
                self._post_public_discovery(
                    form="times",
                    fields={**common, "Date": available_date},
                )
            )
            traces.append(
                RequestTraceEntry(
                    method="POST",
                    operation="times",
                    status_code=times_status,
                    duration_ms=times_ms,
                    response_bytes=times_bytes,
                )
            )
            times = ConfirmedTimesClassifier().classify(
                times_status, times_payload
            )
            if not times.recognized:
                return QueueState(
                    "UNKNOWN",
                    utc_timestamp(),
                    base.page_hash,
                    f"{self.config.city} times response did not match the "
                    "confirmed schema.",
                    "http",
                    tuple(item.value for item in times.evidence),
                    DiscoveryStage.TIMES,
                    available_dates_count=len(days.dates),
                    request_trace=tuple(traces),
                )
            evidence.extend(item.value for item in times.evidence)
            all_times.extend(times.times)

        earliest = min(all_times) if all_times else None
        latest = max(all_times) if all_times else None
        state = "SLOTS_AVAILABLE" if all_times else "POSSIBLE_SLOTS"
        return QueueState(
            state,
            utc_timestamp(),
            base.page_hash,
            (
                f"Available dates: {len(days.dates)}; "
                f"available time slots: {len(all_times)}; "
                f"earliest: {earliest or 'none'}; latest: {latest or 'none'}."
            ),
            "http",
            tuple(dict.fromkeys(evidence)),
            DiscoveryStage.TIMES,
            available_dates_count=len(days.dates),
            available_time_slots_count=len(all_times),
            earliest_available_time=earliest,
            latest_available_time=latest,
            request_trace=tuple(traces),
        )

    @staticmethod
    def normalize_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())

    def classify_state(self, status_code: int, html: str) -> QueueState:
        text = self.normalize_text(html)
        page_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        landing = self.landing_classifier.classify(status_code, html)
        mapping = {
            LandingState.NO_SLOTS: (
                "NO_SLOTS",
                "Landing HTML contains the confirmed no-slots marker.",
            ),
            LandingState.DISCOVERY_READY: (
                "POSSIBLE_SLOTS",
                "Landing evidence permits the guarded days transition.",
            ),
            LandingState.BLOCKED: (
                "BLOCKED",
                "Landing request was blocked or challenged.",
            ),
            LandingState.ERROR: ("ERROR", f"HTTP {status_code}."),
            LandingState.AUTH_REQUIRED: (
                "UNKNOWN",
                "Landing HTML requires authentication.",
            ),
            LandingState.MAINTENANCE: (
                "UNKNOWN",
                "Landing HTML reports maintenance.",
            ),
            LandingState.UNKNOWN: (
                "UNKNOWN",
                "Landing HTML did not match a confirmed provider state.",
            ),
        }
        status, message = mapping[landing.state]
        return QueueState(
            status,
            utc_timestamp(),
            page_hash,
            message,
            "http",
            tuple(item.value for item in landing.evidence),
            DiscoveryStage.LANDING,
        )

    def load_previous_state(self) -> QueueState | None:
        if not self.state_file.exists():
            return None
        try:
            values = json.loads(self.state_file.read_text(encoding="utf-8"))
            values.setdefault("source", "unknown")
            return QueueState(**values)
        except (OSError, json.JSONDecodeError, TypeError):
            logging.exception("Unable to read the previous state.")
            return None

    def save_state(self, state: QueueState) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_file.with_suffix(".tmp")
        payload = asdict(state)
        # Traces belong to immutable Observations, not mutable current state.
        payload.pop("request_trace", None)
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.state_file)

    def configured_diagnostic_events(self) -> set[str]:
        value = os.getenv(
            f"{self.config.env_prefix}_DIAGNOSTIC_EVENTS",
            ",".join(sorted(DEFAULT_DIAGNOSTIC_EVENTS)),
        )
        return {
            event.strip().upper()
            for event in value.split(",")
            if event.strip()
        }

    @staticmethod
    def diagnostic_events_for_transition(
        previous: QueueState | None,
        current: QueueState,
        enabled_events: Iterable[str],
    ) -> list[str]:
        enabled = {event.upper() for event in enabled_events}
        events: list[str] = []
        if current.status in enabled and (
            previous is None or previous.status != current.status
        ):
            events.append(current.status)
        if (
            "HTML_STRUCTURE_CHANGED" in enabled
            and previous is not None
            and previous.page_hash != current.page_hash
            and previous.status == current.status
        ):
            events.append("HTML_STRUCTURE_CHANGED")
        return events

    def check_once(
        self,
        diagnostic_backend: object | None = None,
        diagnostic_events: Iterable[str] | None = None,
    ) -> QueueState:
        del diagnostic_backend
        previous = self.load_previous_state()
        started = time.perf_counter()
        http_status: int | None = None
        observed_status: int | None = None
        response_bytes = 0
        try:
            http_status, html = self.fetch_page()
            response_bytes = len(html.encode("utf-8"))
            landing_duration_ms = round(
                (time.perf_counter() - started) * 1000
            )
            current = self.discover_public_availability(
                landing_status=http_status,
                landing_html=html,
                landing_trace=RequestTraceEntry(
                    method="GET",
                    operation="landing",
                    status_code=http_status,
                    duration_ms=landing_duration_ms,
                    response_bytes=response_bytes,
                ),
            )
            if (
                self.config.public_discovery_profile is None
                and "QUEUE_FORM_FOUND" in current.evidence
                and self.collect_candidate_evidence(
                    html=html,
                    state=current,
                    transport="http",
                )
            ):
                current.status = "UNKNOWN"
                current.message = (
                    "Candidate queue form detected; governance review "
                    "is required before discovery."
                )
            observed_status = http_status
            if current.status == "BLOCKED":
                if self.playwright_fallback_enabled():
                    logging.warning(
                        "HTTP blocked → switching to Playwright"
                    )
                    current, browser_status = self.run_browser_fallback(
                        current
                    )
                    observed_status = browser_status
                elif self.candidate_probe_enabled() and (
                    self.candidate_evidence.should_probe(
                        transport="playwright",
                        page_hash=current.page_hash,
                        cooldown_seconds=self.candidate_probe_cooldown_seconds(),
                    )
                ):
                    self.candidate_evidence.mark_probe(
                        transport="playwright",
                        page_hash=current.page_hash,
                    )
                    logging.warning(
                        "HTTP blocked → starting bounded Playwright "
                        "candidate landing probe"
                    )
                    current, browser_status = self.run_browser_candidate_probe(
                        current
                    )
                    observed_status = browser_status
                else:
                    logging.warning(
                        "HTTP monitoring is blocked. Experimental Playwright "
                        "fallback is disabled."
                    )
            else:
                logging.info("HTTP transport selected")
        except requests.RequestException as error:
            current = QueueState(
                "ERROR",
                utc_timestamp(),
                "",
                f"HTTP request failed: {error}",
                "http",
            )
        except Exception as error:
            logging.exception("HTTP provider check failed.")
            current = QueueState(
                "ERROR",
                utc_timestamp(),
                "",
                f"Provider check failed: {error}",
                "http",
            )

        html_changed = previous is not None and previous.page_hash != current.page_hash
        enabled_events = (
            self.configured_diagnostic_events()
            if diagnostic_events is None
            else diagnostic_events
        )
        requested_events = self.diagnostic_events_for_transition(
            previous, current, enabled_events
        )
        if previous is None:
            logging.info("Initial state: %s via %s.", current.status, current.source)
        elif previous.status != current.status:
            logging.warning(
                "QUEUE STATE CHANGED: %s -> %s | source=%s | reason=%s",
                previous.status,
                current.status,
                current.source,
                current.message,
            )
        elif html_changed:
            logging.info(
                "Page content changed, but queue status remains %s via %s.",
                current.status,
                current.source,
            )
        else:
            logging.info("No change. Current state: %s via %s.", current.status, current.source)

        self.save_state(current)
        recorded = self.observation_service.record(
            provider_id=self.config.provider,
            url=self.config.queue_url,
            observed_at=current.checked_at,
            transport=current.source,
            state=current.status,
            duration_ms=round((time.perf_counter() - started) * 1000),
            http_status=observed_status,
            page_hash=current.page_hash,
            html_changed=html_changed,
            classifier_reason=current.message,
            error_category=current.status if current.status == "ERROR" else None,
            diagnostic_events=requested_events,
            mode=os.getenv("SITE_INVESTIGATOR_MODE", "research"),
            discovery_stage=current.discovery_stage,
            evidence=current.evidence,
            request_trace=current.request_trace,
            available_dates_count=current.available_dates_count,
            available_time_slots_count=current.available_time_slots_count,
            earliest_available_time=current.earliest_available_time,
            latest_available_time=current.latest_available_time,
        )
        if current.discovery_stage == DiscoveryStage.TIMES:
            logging.info(current.message)
        logging.info(
            "Observation recorded. observation_id=%s run_id=%s "
            "diagnostic_decision=%s investigation_id=%s",
            recorded.observation.observation_id,
            recorded.observation.run_id,
            recorded.decision.outcome,
            recorded.decision.investigation_id or "none",
        )
        return current

    def run(self) -> None:
        logging.info("Starting %s queue monitor.", self.config.city)
        initial_delay = max(
            0, int(os.getenv("PROVIDER_INITIAL_DELAY_SECONDS", "0"))
        )
        if initial_delay:
            logging.info(
                "Initial provider check delayed by %s seconds.",
                initial_delay,
            )
            time.sleep(initial_delay)
        diagnostic_events = self.configured_diagnostic_events()
        consecutive_failures = 0
        while True:
            state = self.check_once(None, diagnostic_events)
            consecutive_failures = (
                consecutive_failures + 1
                if state.status in {"BLOCKED", "ERROR"}
                else 0
            )
            base_interval = random.randint(
                MIN_INTERVAL_SECONDS, MAX_INTERVAL_SECONDS
            )
            multiplier = min(2 ** max(consecutive_failures - 1, 0), 4)
            sleep_seconds = base_interval * multiplier
            if state.status == "BLOCKED" and consecutive_failures >= 4:
                blocked_cooldown = max(
                    0,
                    int(
                        os.getenv(
                            "BLOCKED_COOLDOWN_SECONDS",
                            str(DEFAULT_BLOCKED_COOLDOWN_SECONDS),
                        )
                    ),
                )
                sleep_seconds = max(sleep_seconds, blocked_cooldown)
                logging.warning(
                    "HTTP transport remains blocked; applying cooldown of "
                    "at least %s seconds.",
                    blocked_cooldown,
                )
            logging.info(
                "Next check in %s seconds (failure streak: %s).",
                sleep_seconds,
                consecutive_failures,
            )
            time.sleep(sleep_seconds)

    def main(self) -> int:
        self.configure_logging()
        try:
            self.run()
        except KeyboardInterrupt:
            logging.info(
                "Monitoring stopped manually. reason=manual_interrupt signal=Ctrl+C"
            )
            return 130
        return 0
