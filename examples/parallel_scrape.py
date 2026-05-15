"""
Parallel scraping: fetch multiple pages at once using the browser pool.
The pool distributes tasks across browser instances automatically.

Run with:  PYTHONPATH=. python3 examples/parallel_scrape.py
"""
import asyncio
from kryptic import Kryptic

URLS = [
    "https://example.com",
    "https://httpbin.org/html",
    "https://httpbin.org/get",
    "https://example.org",
    "https://iana.org",
    "https://httpbin.org/status/200",
]


def make_scrape_task(url: str):
    async def task(page):
        await page.block_resources(["image", "stylesheet", "font", "media"])
        await page.goto(url, wait_until="domcontentloaded")
        return {
            "url": url,
            "title": await page.title(),
            "final_url": page.url,
        }
    return task


async def main() -> None:
    async with Kryptic(headless=True, concurrency=3) as k:
        print(f"Scraping {len(URLS)} pages with {k.concurrency} browser instances...\n")

        timed = await k.batch_timed([make_scrape_task(u) for u in URLS])

        for r in timed["results"]:
            print(f"  [{r['url']}]  →  {r['title']!r}")

        print(f"\nDone in {timed['total_seconds']}s  "
              f"(avg {timed['avg_seconds']}s per page)")


asyncio.run(main())
