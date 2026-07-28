from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import Response, async_playwright


QUEUE_URL = "https://kortrijk.pasport.org.ua/solutions/e-queue"

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = Path(
    os.getenv("KORTRIJK_BROWSER_PROFILE", BASE_DIR / ".browser-data" / "kortrijk")
)
DATA_DIR = Path(os.getenv("KORTRIJK_DATA_DIR", BASE_DIR / "data"))
SCREENSHOT_PATH = DATA_DIR / "kortrijk-page.png"
HTML_PATH = DATA_DIR / "kortrijk-page.html"
NETWORK_PATH = DATA_DIR / "kortrijk-network.json"

NO_SLOTS_PHRASES = (
    "Наразі всі місця зайняті",
    "Будь ласка, спробуйте в інший час або день",
)

CHALLENGE_PHRASES = (
    "перевірте, що ви людина",
    "підтвердьте, що ви людина",
    "verify you are human",
    "checking your browser",
    "проверка безопасности",
)

CAPTCHA_SELECTORS = (
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    'iframe[src*="turnstile"]',
    ".g-recaptcha",
    ".h-captcha",
    ".cf-turnstile",
    "#challenge-form",
    ".cf-browser-verification",
)


@dataclass(slots=True)
class BrowserCheckResult:
    status: str
    checked_at: str
    page_hash: str
    final_url: str
    page_title: str
    message: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def check_queue() -> BrowserCheckResult:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    network_events: list[dict[str, Any]] = []
    capture_tasks: set[asyncio.Task[None]] = set()

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=env_flag("KORTRIJK_HEADLESS", False),
            viewport={"width": 1440, "height": 1000},
            locale="uk-UA",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        async def capture_response(response: Response) -> None:
            content_type = response.headers.get("content-type", "").lower()
            if (
                "json" not in content_type
                and response.request.resource_type not in {"xhr", "fetch"}
            ):
                return

            event: dict[str, Any] = {
                "url": response.url,
                "status": response.status,
                "resource_type": response.request.resource_type,
                "content_type": content_type,
            }

            try:
                if "json" in content_type:
                    event["payload"] = await response.json()
                else:
                    event["body_preview"] = (await response.text())[:5000]
            except Exception as error:
                event["capture_error"] = str(error)

            network_events.append(event)

        def schedule_response_capture(response: Response) -> None:
            task = asyncio.create_task(capture_response(response))
            capture_tasks.add(task)
            task.add_done_callback(capture_tasks.discard)

        page.on("response", schedule_response_capture)

        try:
            response = await page.goto(
                QUEUE_URL,
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            await page.wait_for_timeout(5_000)

            title = await page.title()
            body_text = await page.locator("body").inner_text()
            html = await page.content()
            final_url = page.url
            page_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()

            await page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            HTML_PATH.write_text(html, encoding="utf-8")

            captcha_visible = False
            for selector in CAPTCHA_SELECTORS:
                locator = page.locator(selector)
                if await locator.count() == 0:
                    continue
                try:
                    if await locator.first.is_visible():
                        captcha_visible = True
                        break
                except Exception:
                    continue

            body_text_lower = body_text.lower()
            challenge_visible = any(
                phrase in body_text_lower for phrase in CHALLENGE_PHRASES
            )
            response_status = response.status if response is not None else None

            if captcha_visible:
                status = "CAPTCHA_REQUIRED"
                message = "A visible CAPTCHA requires user verification."
            elif challenge_visible or response_status in {403, 429, 503}:
                status = "BLOCKED"
                message = "The browser encountered an anti-bot challenge."
            elif response_status is not None and response_status >= 400:
                status = "ERROR"
                message = f"Browser received HTTP {response_status}."
            elif all(phrase in body_text for phrase in NO_SLOTS_PHRASES):
                status = "NO_SLOTS"
                message = "The page reports that all appointment slots are occupied."
            else:
                status = "UNKNOWN"
                message = (
                    "The available evidence did not match a confirmed queue-state "
                    "classifier. Manual verification is required."
                )

            return BrowserCheckResult(
                status=status,
                checked_at=now_utc(),
                page_hash=page_hash,
                final_url=final_url,
                page_title=title,
                message=message,
            )
        finally:
            if capture_tasks:
                await asyncio.gather(*capture_tasks, return_exceptions=True)
            NETWORK_PATH.write_text(
                json.dumps(
                    network_events,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            await context.close()


def check_queue_sync() -> BrowserCheckResult:
    return asyncio.run(check_queue())


async def main() -> None:
    result = await check_queue()
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
