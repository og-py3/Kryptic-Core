"""
Synchronous usage — no asyncio required.
Ideal for scripts, notebooks, and non-async codebases.

Run with:  PYTHONPATH=. python3 examples/sync_usage.py
"""
from kryptic.sync import KrypticSync


def main():
    # ── HTTP mode (no browser) ─────────────────────────────────────────────
    print("=== HTTP mode ===")
    with KrypticSync(mode="http", concurrency=10) as k:
        resp = k.http_get("https://httpbin.org/get")
        print(f"Status: {resp.status}")
        print(f"User-Agent: {resp.json()['headers']['User-Agent']}\n")

    # ── Browser mode ───────────────────────────────────────────────────────
    print("=== Browser mode ===")
    with KrypticSync(headless=True, concurrency=2) as k:

        async def scrape(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return {
                "title": await page.title(),
                "h1": await page.text("h1"),
                "url": page.url,
            }

        result = k.run(scrape)
        print(f"Title: {result['title']}")
        print(f"H1:    {result['h1']}\n")

        # Batch: run three tasks in parallel
        tasks = [scrape, scrape, scrape]
        timed = k.batch_timed(tasks)
        print(f"Batch: {timed['tasks']} tasks in {timed['total_seconds']}s "
              f"(avg {timed['avg_seconds']}s)")


if __name__ == "__main__":
    main()
