"""Capture passive public-page evidence without advancing the booking flow.

This controlled research tool performs one browser navigation and no clicks,
form submissions, identity actions, or booking actions. Runtime evidence must
be written to a Git-ignored output directory.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Response, async_playwright


INTERESTING_SELECTORS = (
    "form",
    '[name="ServiceCenterId"]',
    '[name="ServiceId"]',
    '[name="Date"]',
    '[class*="calendar"]',
    '[class*="date"]',
    '[class*="time"]',
    '[data-date]',
    '[data-time]',
    '[id*="calendar"]',
    '[id*="date"]',
    '[id*="time"]',
    '[href*="bankid"]',
    '[href*="diia"]',
)


@dataclass(frozen=True, slots=True)
class ResponseSummary:
    method: str
    host: str
    path: str
    status: int
    resource_type: str
    content_type: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_response_summary(response: Response) -> ResponseSummary:
    parsed = urlsplit(response.url)
    host = parsed.hostname or ""
    path = parsed.path
    if (
        "/cdn-cgi/challenge-platform/" in path
        or host == "challenges.cloudflare.com"
        or not host
    ):
        path = "/[challenge-path-redacted]"
    return ResponseSummary(
        method=response.request.method,
        host=host,
        path=path,
        status=response.status,
        resource_type=response.request.resource_type,
        content_type=response.headers.get("content-type", "").split(";", 1)[0],
    )


async def capture(city: str, url: str, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    responses: list[ResponseSummary] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="uk-UA",
            viewport={"width": 1440, "height": 1000},
        )
        page = await context.new_page()
        page.on("response", lambda response: responses.append(
            safe_response_summary(response)
        ))

        navigation = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        await page.wait_for_timeout(5_000)

        html = await page.content()
        body_text = await page.locator("body").inner_text()
        fragments = await page.locator(
            ",".join(INTERESTING_SELECTORS)
        ).evaluate_all(
            """elements => elements.slice(0, 100).map(element => ({
                tag: element.tagName.toLowerCase(),
                id: element.id || null,
                name: element.getAttribute('name'),
                type: element.getAttribute('type'),
                classes: Array.from(element.classList).slice(0, 8),
                text: (element.innerText || element.textContent || '')
                    .replace(/\\s+/g, ' ').trim().slice(0, 500)
            }))"""
        )

        screenshot_path = output_dir / f"{city}-landing.png"
        html_path = output_dir / f"{city}-landing.html"
        dom_path = output_dir / f"{city}-dom-fragments.json"
        network_path = output_dir / f"{city}-network-summary.json"
        report_path = output_dir / f"{city}-capture-summary.json"

        await page.screenshot(path=str(screenshot_path), full_page=True)
        html_path.write_text(html, encoding="utf-8")
        dom_path.write_text(
            json.dumps(fragments, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        network_path.write_text(
            json.dumps(
                [asdict(item) for item in responses],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result: dict[str, object] = {
            "captured_at": utc_now(),
            "city": city,
            "requested_url": url,
            "final_url": page.url,
            "http_status": navigation.status if navigation else None,
            "title": await page.title(),
            "body_hash": hashlib.sha256(
                body_text.encode("utf-8")
            ).hexdigest(),
            "body_text_preview": " ".join(body_text.split())[:1000],
            "interesting_fragment_count": len(fragments),
            "interaction_count": 0,
            "form_submission_count": 0,
            "identity_verification_attempted": False,
            "booking_attempted": False,
        }
        report_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        await context.close()
        await browser.close()
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = asyncio.run(capture(args.city, args.url, args.output))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
