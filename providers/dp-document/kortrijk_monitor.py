from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from kortrijk_browser_spike import check_queue_sync


QUEUE_URL = "https://kortrijk.pasport.org.ua/solutions/e-queue"

MIN_INTERVAL_SECONDS = 7 * 60
MAX_INTERVAL_SECONDS = 12 * 60
REQUEST_TIMEOUT_SECONDS = 30
BLOCKED_HTTP_STATUSES = {403, 429, 503}

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("KORTRIJK_DATA_DIR", BASE_DIR / "data"))
LOG_DIR = Path(os.getenv("KORTRIJK_LOG_DIR", BASE_DIR / "logs"))
STATE_FILE = DATA_DIR / "kortrijk_state.json"
LOG_FILE = LOG_DIR / "kortrijk_monitor.log"

NO_SLOTS_PHRASES = (
    "Наразі всі місця зайняті",
    "Будь ласка, спробуйте в інший час або день",
)

CAPTCHA_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cloudflare",
    "turnstile",
)


@dataclass(slots=True)
class QueueState:
    status: str
    checked_at: str
    page_hash: str
    message: str
    source: str


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
    lowercase_html = html.lower()
    page_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    if status_code in BLOCKED_HTTP_STATUSES:
        return QueueState(
            status="BLOCKED",
            checked_at=current_timestamp(),
            page_hash=page_hash,
            message=f"HTTP {status_code}: anti-bot protection or throttling.",
            source="http",
        )

    if status_code >= 400:
        return QueueState(
            status="ERROR",
            checked_at=current_timestamp(),
            page_hash=page_hash,
            message=f"HTTP request failed with status {status_code}.",
            source="http",
        )

    if any(marker in lowercase_html for marker in CAPTCHA_MARKERS):
        return QueueState(
            status="BLOCKED",
            checked_at=current_timestamp(),
            page_hash=page_hash,
            message="CAPTCHA or anti-bot marker detected.",
            source="http",
        )

    if all(phrase in normalized_text for phrase in NO_SLOTS_PHRASES):
        return QueueState(
            status="NO_SLOTS",
            checked_at=current_timestamp(),
            page_hash=page_hash,
            message="Official page reports that all appointment slots are occupied.",
            source="http",
        )

    return QueueState(
        status="POSSIBLE_SLOTS",
        checked_at=current_timestamp(),
        page_hash=page_hash,
        message=(
            "The known no-slots message was not found. "
            "Manual verification is required."
        ),
        source="http",
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


def report_change(previous: QueueState | None, current: QueueState) -> None:
    if previous is None:
        logging.info(
            "Initial state: %s via %s | %s",
            current.status,
            current.source,
            current.message,
        )
    elif previous.status != current.status:
        logging.warning(
            "QUEUE STATE CHANGED: %s -> %s via %s | %s",
            previous.status,
            current.status,
            current.source,
            current.message,
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


def browser_fallback() -> QueueState:
    result = check_queue_sync()
    return QueueState(
        status=result.status,
        checked_at=result.checked_at,
        page_hash=result.page_hash,
        message=result.message,
        source="playwright",
    )


def check_once() -> QueueState:
    previous_state = load_previous_state()

    try:
        status_code, html = fetch_page()
        current_state = classify_state(status_code, html)
        if current_state.status == "BLOCKED":
            logging.warning(
                "HTTP provider is blocked; starting Playwright fallback."
            )
            current_state = browser_fallback()
    except requests.RequestException as error:
        current_state = QueueState(
            status="ERROR",
            checked_at=current_timestamp(),
            page_hash="",
            message=f"HTTP request failed: {error}",
            source="http",
        )
    except Exception as error:
        logging.exception("Playwright fallback failed.")
        current_state = QueueState(
            status="ERROR",
            checked_at=current_timestamp(),
            page_hash="",
            message=f"Provider check failed: {error}",
            source="playwright",
        )

    report_change(previous_state, current_state)
    save_state(current_state)
    return current_state


def run_monitor() -> None:
    logging.info("Starting Kortrijk queue monitor.")
    logging.info(
        "Random check interval: %s-%s seconds.",
        MIN_INTERVAL_SECONDS,
        MAX_INTERVAL_SECONDS,
    )

    consecutive_failures = 0
    while True:
        state = check_once()

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


def main() -> None:
    configure_logging()
    run_monitor()


if __name__ == "__main__":
    main()
