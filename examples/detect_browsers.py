"""
Auto-detect which browsers are installed and distribute work across all of them.

Run with:  PYTHONPATH=. python3 examples/detect_browsers.py
"""
import asyncio
from kryptic import Kryptic, detect_browsers
from kryptic.types import BrowserTypeName


async def main() -> None:
    print("Detecting installed browsers...")
    browser_infos = await detect_browsers()

    available: list[BrowserTypeName] = [
        b["name"] for b in browser_infos if b["available"]
    ]
    unavailable = [b["name"] for b in browser_infos if not b["available"]]

    print(f"  Available  : {available}")
    print(f"  Unavailable: {unavailable}\n")

    if not available:
        print("No browsers found. Run: python3 -m playwright install chromium")
        return

    async with Kryptic(
        headless=True,
        concurrency=len(available),
        browser_types=available,
    ) as k:
        print(f"Pool: {k}\n")

        urls = ["https://example.com", "https://example.org", "https://iana.org"]

        def make_task(url: str):
            async def task(page):
                await page.block_resources(["image", "stylesheet", "font"])
                await page.goto(url)
                return {"url": url, "title": await page.title()}
            return task

        results = await k.batch([make_task(u) for u in urls])
        for r in results:
            print(f"  {r['url']}  →  {r['title']!r}")


asyncio.run(main())
