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
from monitor_metadata import utc_timestamp
from provider_protocol import DiscoveryStage, LandingPageClassifier, LandingState


MIN_INTERVAL_SECONDS = 7 * 60
MAX_INTERVAL_SECONDS = 12 * 60
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_DIAGNOSTIC_EVENTS = {
    "BLOCKED",
    "UNKNOWN",
    "HTML_STRUCTURE_CHANGED",
    "QUEUE_SECTION_CHANGED",
}


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    city: str
    provider: str
    queue_url: str
    env_prefix: str
    base_dir: Path
    project_dir: Path | None = None

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
        response = requests.get(
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
        temporary.write_text(
            json.dumps(asdict(state), ensure_ascii=False, indent=2),
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
        response_bytes = 0
        try:
            http_status, html = self.fetch_page()
            response_bytes = len(html.encode("utf-8"))
            current = self.classify_state(http_status, html)
            if current.status == "BLOCKED":
                logging.warning(
                    "HTTP monitoring is blocked. Browser execution is reserved "
                    "for the separate diagnostic worker."
                )
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
            http_status=http_status,
            page_hash=current.page_hash,
            html_changed=html_changed,
            classifier_reason=current.message,
            error_category=current.status if current.status == "ERROR" else None,
            diagnostic_events=requested_events,
            mode=os.getenv("SITE_INVESTIGATOR_MODE", "research"),
            discovery_stage=current.discovery_stage,
            evidence=current.evidence,
            request_trace=(
                RequestTraceEntry(
                    method="GET",
                    operation="landing",
                    status_code=http_status,
                    duration_ms=round((time.perf_counter() - started) * 1000),
                    response_bytes=response_bytes,
                ),
            ),
        )
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
