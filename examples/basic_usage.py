"""
Basic usage: open a page, grab its title and some text.
Run with:  PYTHONPATH=. python3 examples/basic_usage.py
"""
import asyncio
from kryptic import Kryptic


async def main() -> None:
    async with Kryptic(headless=True, concurrency=2) as k:
        print(f"Pool ready: {k}")

        async def get_title(page):
            await page.goto("https://example.com")
            return await page.title()

        title = await k.run(get_title)
        print(f"Title: {title}")

        async def fast_scrape(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            heading = await page.text("h1")
            return {"title": await page.title(), "h1": heading}

        result = await k.run(fast_scrape)
        print(f"Result: {result}")


asyncio.run(main())
