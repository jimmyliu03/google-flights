from typing import Any
import asyncio
from playwright.async_api import async_playwright

async def fetch_with_playwright(url: str) -> str:
    async with async_playwright() as p:
        # Launch with anti-detection settings
        browser = await p.chromium.launch(
            args=['--disable-blink-features=AutomationControlled']
        )
        # Create context with realistic user agent
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # Remove webdriver property to avoid detection
        await page.add_init_script('delete Object.getPrototypeOf(navigator).webdriver')

        await page.goto(url)
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')

        # Wait for flight results (try multiple selectors)
        try:
            await page.wait_for_selector('.eQ35Ce', timeout=30000)
        except:
            # Try waiting for any flight list item instead
            await page.wait_for_selector('li.pIav2d', timeout=30000)

        # Wait for page to fully load before looking for "View more flights"
        await page.wait_for_timeout(5000)

        # Click ALL "View more flights" buttons (there can be multiple in Best + Cheapest sections)
        try:
            buttons = await page.locator('span.bEfgkb:has-text("View more flights")').all()
            for btn in buttons:
                try:
                    await btn.click()
                    await page.wait_for_timeout(2000)
                except:
                    pass  # Button may have become stale, continue
        except:
            pass  # No buttons found, continue

        body = await page.evaluate(
            "() => document.querySelector('[role=\"main\"]').innerHTML"
        )
        await browser.close()
    return body

def local_playwright_fetch(params: dict) -> Any:
    url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())
    body = asyncio.run(fetch_with_playwright(url))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse
