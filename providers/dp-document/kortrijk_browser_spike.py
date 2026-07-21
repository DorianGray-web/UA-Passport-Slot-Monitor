from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright


QUEUE_URL = "https://kortrijk.pasport.org.ua/solutions/e-queue"
PROFILE_DIR = Path(".browser-data/kortrijk")
SCREENSHOT_PATH = Path("data/kortrijk-page.png")
HTML_PATH = Path("data/kortrijk-page.html")
NETWORK_PATH = Path("data/kortrijk-network.json")

NO_SLOTS_PHRASES = (
    "Наразі всі місця зайняті",
    "Будь ласка, спробуйте в інший час або день",
)


@dataclass(slots=True)
class BrowserCheckResult:
    status: str
    checked_at: str
    final_url: str
    page_title: str
    message: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


async def check_queue() -> BrowserCheckResult:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 1000},
            locale="uk-UA",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        network_events: list[dict[str, object]] = []

        async def capture_response(response) -> None:
            content_type = response.headers.get("content-type", "").lower()

            is_interesting = (
                "json" in content_type
                or response.request.resource_type in {"xhr", "fetch"}
            )

            if not is_interesting:
                return

            event: dict[str, object] = {
                "url": response.url,
                "status": response.status,
                "resource_type": response.request.resource_type,
                "content_type": content_type,
            }

            try:
                if "json" in content_type:
                    event["payload"] = await response.json()
                else:
                    text = await response.text()
                    event["body_preview"] = text[:5000]
            except Exception as error:
                event["capture_error"] = str(error)

            network_events.append(event)


        def schedule_response_capture(response) -> None:
            asyncio.create_task(capture_response(response))


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
            print("\n--- PAGE TEXT PREVIEW ---")
            print(body_text[:2000])
            print("--- END PREVIEW ---\n")
            html = await page.content()
            final_url = page.url

            await page.screenshot(
                path=str(SCREENSHOT_PATH),
                full_page=True,
            )
            HTML_PATH.write_text(html, encoding="utf-8")

            NETWORK_PATH.write_text(
                json.dumps(
                    network_events,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            captcha_selectors = (
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                'iframe[src*="turnstile"]',
                '.g-recaptcha',
                '.h-captcha',
                '.cf-turnstile',
                '#challenge-form',
                '.cf-browser-verification',)

            captcha_visible = False

            for selector in captcha_selectors:
                locator = page.locator(selector)

                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible():
                            captcha_visible = True
                            break
                    except Exception:
                        continue           

            challenge_phrases = (
                "перевірте, що ви людина",
                "підтвердьте, що ви людина",
                "verify you are human",
                "checking your browser",
                "проверка безопасности",
            )

            challenge_text_visible = any(
                phrase in body_text.lower()
                for phrase in challenge_phrases
    )

            if all(phrase in body_text for phrase in NO_SLOTS_PHRASES):
                status = "NO_SLOTS"
                message = "The page reports that all appointment slots are occupied."

            elif captcha_visible or challenge_text_visible:
                status = "CAPTCHA"
                message = "A visible CAPTCHA or anti-bot challenge was detected."

            elif response is not None and response.status >= 400:
                status = "HTTP_ERROR"
                message = f"Browser received HTTP {response.status}."

            else:
                status = "UNKNOWN"
                message = (
                    "Neither the known no-slots message nor a visible CAPTCHA "
                    "was detected. Manual review is required."
        )

            return BrowserCheckResult(
                status=status,
                checked_at=now_utc(),
                final_url=final_url,
                page_title=title,
                message=message,
            )

        finally:
            await context.close()


async def main() -> None:
    result = await check_queue()
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
