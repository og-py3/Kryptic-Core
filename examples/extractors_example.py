"""
Extractors — pull structured data from pages automatically.

Run with:  PYTHONPATH=. python3 examples/extractors_example.py
"""
import asyncio
import json
from kryptic import Kryptic
from kryptic import extractors


async def main():
    async with Kryptic(headless=True, concurrency=1) as k:

        async def task(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")

            links = await extractors.extract_links(page)
            meta = await extractors.extract_meta(page)
            headings = await extractors.extract_headings(page)
            text = await extractors.extract_text(page)
            emails = await extractors.extract_emails(page)

            return {
                "meta": meta,
                "headings": headings,
                "links": links[:5],
                "text_preview": text[:200],
                "emails": emails,
            }

        data = await k.run(task)

        print("=== Meta ===")
        for k2, v in data["meta"].items():
            print(f"  {k2}: {v}")

        print("\n=== Headings ===")
        for level, texts in data["headings"].items():
            print(f"  {level}: {texts}")

        print("\n=== Links (first 5) ===")
        for l in data["links"]:
            print(f"  [{l['text']}] → {l['href']}")

        print(f"\n=== Text preview ===\n  {data['text_preview']}")
        print(f"\n=== Emails found: {data['emails']}")

        # Full snapshot
        async def full_snap(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await extractors.snapshot(page)

        snap = await k.run(full_snap)
        print("\n=== Full snapshot keys ===")
        for key, val in snap.items():
            print(f"  {key}: {type(val).__name__} ({len(val) if hasattr(val, '__len__') else val})")


asyncio.run(main())
