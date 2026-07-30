from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

QUEUE_URL = "https://kortrijk.pasport.org.ua/solutions/e-queue"
PROVIDER_NAME = "dp-document-kortrijk"

MIN_INTERVAL_SECONDS = 7 * 60
MAX_INTERVAL_SECONDS = 12 * 60
REQUEST_TIMEOUT_SECONDS = 30

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from diagnostics.domain import RequestTraceEntry, make_run_id  # noqa: E402
from diagnostics.event_store import SQLiteEventStore  # noqa: E402
from diagnostics.monitoring import ObservationService  # noqa: E402
from provider_protocol import (  # noqa: E402
    DiscoveryStage,
    LandingPageClassifier,
    LandingState,
)

DATA_DIR = Path(os.getenv("KORTRIJK_DATA_DIR", BASE_DIR / "data"))
LOG_DIR = Path(os.getenv("KORTRIJK_LOG_DIR", PROJECT_DIR / "logs"))
METADATA_DIR = Path(
    os.getenv("KORTRIJK_METADATA_DIR", PROJECT_DIR / "metadata")
)
STATE_FILE = DATA_DIR / "kortrijk_state.json"
LOG_FILE = LOG_DIR / "kortrijk.log"
METADATA_FILE = METADATA_DIR / "kortrijk.jsonl"
OBSERVATION_STORE_PATH = Path(
    os.getenv(
        "OBSERVATION_STORE_PATH",
        PROJECT_DIR / "data" / "observations.sqlite3",
    )
)

DEFAULT_DIAGNOSTIC_EVENTS = {
    "BLOCKED",
    "UNKNOWN",
    "HTML_STRUCTURE_CHANGED",
    "QUEUE_SECTION_CHANGED",
}

_OBSERVATION_SERVICE: ObservationService | None = None
LANDING_CLASSIFIER = LandingPageClassifier(
    os.getenv("KORTRIJK_CSRF_FIELD") or None
)


def observation_service() -> ObservationService:
    global _OBSERVATION_SERVICE
    if _OBSERVATION_SERVICE is None:
        _OBSERVATION_SERVICE = ObservationService(
            SQLiteEventStore(OBSERVATION_STORE_PATH),
            run_id=os.getenv("MONITOR_RUN_ID", make_run_id()),
            jsonl_export=METADATA_FILE,
        )
    return _OBSERVATION_SERVICE


@dataclass(slots=True)
class QueueState:
    status: str
    checked_at: str
    page_hash: str
    message: str
    source: str
    evidence: tuple[str, ...] = ()
    discovery_stage: str = DiscoveryStage.LANDING


def configure_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def next_interval_seconds() -> int:
    return random.randint(MIN_INTERVAL_SECONDS, MAX_INTERVAL_SECONDS)


def fetch_page() -> tuple[int, str]:
    headers = {
        "User-Agent": (
            "UA-Passport-Slot-Monitor/0.2 "
            "(research prototype; contact via GitHub)"
        ),
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
    }
    response = requests.get(
        QUEUE_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    return response.status_code, response.text


def normalize_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_state(status_code: int, html: str) -> QueueState:
    normalized_text = normalize_text(html)
    page_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    landing = LANDING_CLASSIFIER.classify(status_code, html)
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
        current_timestamp(),
        page_hash,
        message,
        "http",
        tuple(item.value for item in landing.evidence),
        DiscoveryStage.LANDING,
    )


def load_previous_state() -> QueueState | None:
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        data.setdefault("source", "unknown")
        return QueueState(**data)
    except (OSError, json.JSONDecodeError, TypeError):
        logging.exception("Unable to read the previous state.")
        return None


def save_state(state: QueueState) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = STATE_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(asdict(state), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_file.replace(STATE_FILE)


def transition_reason(previous: QueueState, current: QueueState) -> str:
    """Describe why a normalized queue-state transition was accepted."""
    unresolved_states = {"BLOCKED", "CAPTCHA_REQUIRED", "UNKNOWN", "ERROR"}
    recognized_states = {"NO_SLOTS", "POSSIBLE_SLOTS", "SLOTS_AVAILABLE"}
    if (
        previous.status in unresolved_states
        and current.status in recognized_states
    ):
        return (
            f"Queue page restored to recognized state {current.status}. "
            f"{current.message}"
        )
    return current.message


def report_change(
    previous: QueueState | None,
    current: QueueState,
    diagnostic_events: Iterable[str] = (),
    *,
    diagnostic_backend_available: bool = False,
) -> None:
    diagnostic_event_list = list(diagnostic_events)
    if previous is None:
        logging.info(
            "Initial state: %s via %s | %s",
            current.status,
            current.source,
            current.message,
        )
    elif previous.status != current.status:
        diagnostic_status = (
            "triggered"
            if diagnostic_backend_available and diagnostic_event_list
            else "not_triggered"
        )
        logging.warning(
            "QUEUE STATE CHANGED: %s -> %s "
            "| source=%s | reason=%s | diagnostic=%s | diagnostic_events=%s",
            previous.status,
            current.status,
            current.source,
            transition_reason(previous, current),
            diagnostic_status,
            ",".join(diagnostic_event_list) or "none",
        )
    elif previous.page_hash != current.page_hash:
        logging.info(
            "Page content changed, but queue status remains %s via %s.",
            current.status,
            current.source,
        )
    else:
        logging.info(
            "No change. Current state: %s via %s.",
            current.status,
            current.source,
        )


def configured_diagnostic_events() -> set[str]:
    value = os.getenv(
        "KORTRIJK_DIAGNOSTIC_EVENTS",
        ",".join(sorted(DEFAULT_DIAGNOSTIC_EVENTS)),
    )
    return {event.strip().upper() for event in value.split(",") if event.strip()}


def diagnostic_events_for_transition(
    previous: QueueState | None,
    current: QueueState,
    enabled_events: Iterable[str],
) -> list[str]:
    """Return configured diagnostic events that are new for this observation."""
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
    diagnostic_backend: object | None = None,
    diagnostic_events: Iterable[str] | None = None,
) -> QueueState:
    del diagnostic_backend
    previous_state = load_previous_state()
    started = time.perf_counter()
    http_status: int | None = None
    response_bytes = 0

    try:
        http_status, html = fetch_page()
        response_bytes = len(html.encode("utf-8"))
        current_state = classify_state(http_status, html)
        if current_state.status == "BLOCKED":
            logging.warning(
                "HTTP monitoring is blocked. Browser execution is reserved "
                "for the separate diagnostic worker."
            )
    except requests.RequestException as error:
        current_state = QueueState(
            status="ERROR",
            checked_at=current_timestamp(),
            page_hash="",
            message=f"HTTP request failed: {error}",
            source="http",
        )
    except Exception as error:
        logging.exception("HTTP provider check failed.")
        current_state = QueueState(
            status="ERROR",
            checked_at=current_timestamp(),
            page_hash="",
            message=f"Provider check failed: {error}",
            source="http",
        )

    enabled_diagnostic_events = (
        configured_diagnostic_events()
        if diagnostic_events is None
        else diagnostic_events
    )
    requested_diagnostic_events = diagnostic_events_for_transition(
        previous_state,
        current_state,
        enabled_diagnostic_events,
    )
    report_change(
        previous_state,
        current_state,
        requested_diagnostic_events,
        diagnostic_backend_available=bool(requested_diagnostic_events),
    )
    save_state(current_state)
    recorded = observation_service().record(
        provider_id=PROVIDER_NAME,
        url=QUEUE_URL,
        observed_at=current_state.checked_at,
        transport=current_state.source,
        state=current_state.status,
        duration_ms=round((time.perf_counter() - started) * 1000),
        http_status=http_status,
        page_hash=current_state.page_hash,
        html_changed=(
            previous_state is not None
            and previous_state.page_hash != current_state.page_hash
        ),
        classifier_reason=(
            transition_reason(previous_state, current_state)
            if previous_state is not None
            else current_state.message
        ),
        error_category=(
            current_state.status if current_state.status == "ERROR" else None
        ),
        diagnostic_events=requested_diagnostic_events,
        mode=os.getenv("SITE_INVESTIGATOR_MODE", "research"),
        discovery_stage=current_state.discovery_stage,
        evidence=current_state.evidence,
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
    return current_state


def run_monitor() -> None:
    logging.info("Starting Kortrijk queue monitor.")
    logging.info(
        "Random check interval: %s-%s seconds.",
        MIN_INTERVAL_SECONDS,
        MAX_INTERVAL_SECONDS,
    )

    diagnostic_events = configured_diagnostic_events()
    logging.info(
        "Diagnostic policy events: %s.",
        ", ".join(sorted(diagnostic_events)),
    )

    consecutive_failures = 0
    while True:
        state = check_once(None, diagnostic_events)

        if state.status in {"BLOCKED", "ERROR"}:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        base_interval = next_interval_seconds()
        backoff_multiplier = min(2 ** max(consecutive_failures - 1, 0), 4)
        sleep_seconds = base_interval * backoff_multiplier
        logging.info(
            "Next check in %s seconds (failure streak: %s).",
            sleep_seconds,
            consecutive_failures,
        )
        time.sleep(sleep_seconds)


def main() -> int:
    configure_logging()
    try:
        run_monitor()
    except KeyboardInterrupt:
        logging.info(
            "Monitoring stopped manually. reason=manual_interrupt "
            "signal=Ctrl+C"
        )
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
