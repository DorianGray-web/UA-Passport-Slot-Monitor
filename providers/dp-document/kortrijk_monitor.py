from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


QUEUE_URL = "https://kortrijk.pasport.org.ua/solutions/e-queue"

CHECK_INTERVAL_SECONDS = 15 * 60
REQUEST_TIMEOUT_SECONDS = 30

STATE_FILE = Path("data/kortrijk_state.json")
LOG_FILE = Path("logs/kortrijk_monitor.log")

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


def fetch_page() -> str:
    headers = {
        "User-Agent": (
            "UA-Passport-Slot-Monitor/0.1 "
            "(research prototype; contact via GitHub)"
        ),
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
    }

    response = requests.get(
        QUEUE_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return response.text


def normalize_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    return " ".join(soup.get_text(" ", strip=True).split())


def classify_state(html: str) -> QueueState:
    normalized_text = normalize_text(html)
    lowercase_html = html.lower()

    page_hash = hashlib.sha256(
        normalized_text.encode("utf-8")
    ).hexdigest()

    if any(marker in lowercase_html for marker in CAPTCHA_MARKERS):
        return QueueState(
            status="CAPTCHA",
            checked_at=current_timestamp(),
            page_hash=page_hash,
            message="CAPTCHA or anti-bot marker detected.",
        )

    if all(phrase in normalized_text for phrase in NO_SLOTS_PHRASES):
        return QueueState(
            status="NO_SLOTS",
            checked_at=current_timestamp(),
            page_hash=page_hash,
            message="Official page reports that all appointment slots are occupied.",
        )

    return QueueState(
        status="POSSIBLE_SLOTS",
        checked_at=current_timestamp(),
        page_hash=page_hash,
        message=(
            "The known no-slots message was not found. "
            "Manual verification is required."
        ),
    )


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_previous_state() -> QueueState | None:
    if not STATE_FILE.exists():
        return None

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return QueueState(**data)
    except (OSError, json.JSONDecodeError, TypeError):
        logging.exception("Unable to read the previous state.")
        return None


def save_state(state: QueueState) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = STATE_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(
            asdict(state),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary_file.replace(STATE_FILE)


def report_change(
    previous: QueueState | None,
    current: QueueState,
) -> None:
    if previous is None:
        logging.info(
            "Initial state: %s | %s",
            current.status,
            current.message,
        )
        return

    if previous.status != current.status:
        logging.warning(
            "QUEUE STATE CHANGED: %s -> %s | %s",
            previous.status,
            current.status,
            current.message,
        )
        return

    if previous.page_hash != current.page_hash:
        logging.info(
            "Page content changed, but queue status remains %s.",
            current.status,
        )
        return

    logging.info("No change. Current state: %s.", current.status)


def check_once() -> QueueState:
    previous_state = load_previous_state()

    try:
        html = fetch_page()
        current_state = classify_state(html)
    except requests.RequestException as error:
        current_state = QueueState(
            status="ERROR",
            checked_at=current_timestamp(),
            page_hash="",
            message=f"Request failed: {error}",
        )

    report_change(previous_state, current_state)
    save_state(current_state)

    return current_state


def run_monitor() -> None:
    logging.info("Starting Kortrijk queue monitor.")
    logging.info("Check interval: %s seconds.", CHECK_INTERVAL_SECONDS)

    while True:
        check_once()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    configure_logging()
    state = check_once()
print(json.dumps(asdict(state), ensure_ascii=False, indent=2))
