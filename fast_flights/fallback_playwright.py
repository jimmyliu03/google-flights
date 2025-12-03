from typing import Any

from .primp import Client

CODE = """\
import asyncio
import sys
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("%s")
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
        locator = page.locator('.eQ35Ce')
        await locator.wait_for()

        # Wait for page to fully load before looking for "View more flights"
        await page.wait_for_timeout(5000)

        # Click "View more flights" if present (for long trips that hide additional results)
        try:
            view_more = page.locator('text="View more flights"')
            if await view_more.is_visible(timeout=10000):
                await view_more.click()
                await page.wait_for_timeout(3000)
        except:
            pass

        body = await page.evaluate(
            \"\"\"() => {
                return document.querySelector('[role="main"]').innerHTML
            }\"\"\"
        )
        await browser.close()
    sys.stdout.write(body)

asyncio.run(main())
"""


def fallback_playwright_fetch(params: dict) -> Any:
    client = Client(impersonate="chrome_100", verify=False)

    res = client.post(
        "https://try.playwright.tech/service/control/run",
        json={
            "code": CODE
            % (
                "https://www.google.com/travel/flights"
                + "?"
                + "&".join(f"{k}={v}" for k, v in params.items())
            ),
            "language": "python",
        },
    )
    assert res.status_code == 200, f"{res.status_code} Result: {res.text_markdown}"
    import json

    class DummyResponse:
        status_code = 200
        text = json.loads(res.text)["output"]
        text_markdown = text

    return DummyResponse
