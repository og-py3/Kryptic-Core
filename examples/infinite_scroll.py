"""
Infinite scroll — keep scrolling until all content is loaded.

Run with:  PYTHONPATH=. python3 examples/infinite_scroll.py
"""
import asyncio
from kryptic import Kryptic


async def main():
    async with Kryptic(headless=True, concurrency=1) as k:

        # Example with a page that has multiple items after scrolling
        async def scroll_and_collect(page):
            await page.block_resources(["image", "font", "media"])
            await page.goto("https://quotes.toscrape.com/scroll", wait_until="domcontentloaded")

            # Scroll until no new quotes appear (up to 5 scrolls)
            scrolls = await page.infinite_scroll(max_scrolls=5, pause=1.5)
            print(f"  Performed {scrolls} scroll(s)")

            # Collect all loaded quotes
            quote_elements = await page.find(".quote .text")
            quotes = [await el.text() for el in quote_elements]
            return quotes

        print("Collecting quotes via infinite scroll...")
        quotes = await k.run(scroll_and_collect)

        print(f"Loaded {len(quotes)} quotes:")
        for i, q in enumerate(quotes[:5], 1):
            print(f"  {i}. {q[:80]}")
        if len(quotes) > 5:
            print(f"  ... and {len(quotes) - 5} more")


asyncio.run(main())
