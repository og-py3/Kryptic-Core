"""
Stealth mode — randomise browser fingerprint to reduce bot detection.

Run with:  PYTHONPATH=. python3 examples/stealth_mode.py
"""
import asyncio
from kryptic import Kryptic
from kryptic.stealth import StealthProfile, random_profile


async def main():
    profile = random_profile(level="high")
    print(f"Profile: {profile}")

    async with Kryptic(headless=True, concurrency=1) as k:

        async def stealth_task(page):
            await profile.apply(page)
            await page.block_resources(["image", "font", "media"])
            await page.goto("https://httpbin.org/user-agent")
            ua_resp = await page.text("pre")
            return {"user_agent": ua_resp}

        result = await k.run(stealth_task)
        print(f"Reported UA: {result['user_agent'][:100]}")

        # Per-task random profiles — each task gets a different fingerprint
        async def random_ua_task(page):
            p = random_profile("medium")
            await p.apply(page)
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://httpbin.org/user-agent")
            return await page.text("pre")

        print("\nRandom profiles across batch:")
        tasks = [random_ua_task] * 3
        results = await k.batch(tasks)
        for i, r in enumerate(results, 1):
            print(f"  Task {i}: {r[:80]}")


asyncio.run(main())
