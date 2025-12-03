import os
import asyncio
from typing import Any


def browserless_fetch(params: dict) -> Any:
    """Fetch Google Flights data using Browserless.io Playwright service.

    Requires BROWSERLESS_API_KEY environment variable.
    """
    api_key = os.environ.get("BROWSERLESS_API_KEY")
    if not api_key:
        raise ValueError("BROWSERLESS_API_KEY environment variable is required")

    # Construct Google Flights URL
    url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())

    body = asyncio.run(_fetch_with_browserless(url, api_key))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse


async def _fetch_with_browserless(url: str, api_key: str) -> str:
    """Connect to Browserless.io via Playwright and fetch the page."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # Connect to Browserless.io via CDP
        browser = await p.chromium.connect_over_cdp(
            f"wss://production-sfo.browserless.io?token={api_key}"
        )

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(url)

        # Handle consent page if redirected
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
            await page.wait_for_timeout(2000)

        # Wait for flight results
        locator = page.locator('.eQ35Ce')
        await locator.wait_for(timeout=30000)

        # Wait for page to fully load
        await page.wait_for_timeout(5000)

        # Click "View more flights" if present (for long trips)
        try:
            view_more = page.locator('text="View more flights"')
            if await view_more.is_visible(timeout=10000):
                await view_more.click()
                await page.wait_for_timeout(3000)
        except:
            pass  # Button not present, continue

        # Extract main content
        body = await page.evaluate(
            '() => document.querySelector(\'[role="main"]\').innerHTML'
        )

        await browser.close()

    return body
