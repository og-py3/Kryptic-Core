"""
Cookie & storage persistence — save and restore browser sessions.

Run with:  PYTHONPATH=. python3 examples/storage_persistence.py
"""
import asyncio
import os
from kryptic import Kryptic
from kryptic.storage import (
    save_cookies,
    load_cookies,
    save_storage_state,
    get_local_storage,
    set_local_storage,
    clear_local_storage,
)

COOKIE_FILE = "/tmp/kryptic_cookies.json"
STATE_FILE  = "/tmp/kryptic_state.json"


async def main():
    async with Kryptic(headless=True, concurrency=1) as k:

        # ── 1. Visit a page, save cookies ───────────────────────────────────
        async def save_session(page):
            await page.goto("https://httpbin.org/cookies/set/kryptic/test123")
            cookies = await save_cookies(page, COOKIE_FILE)
            return [c["name"] for c in cookies]

        cookie_names = await k.run(save_session)
        print(f"Saved cookies: {cookie_names}")

        # ── 2. New session, restore cookies ─────────────────────────────────
        async def restore_and_check(page):
            await load_cookies(page, COOKIE_FILE)
            await page.goto("https://httpbin.org/cookies")
            body = await page.text("pre")
            return body

        body = await k.run(restore_and_check)
        print(f"Cookies sent after restore: {body[:200]}")

        # ── 3. localStorage manipulation ─────────────────────────────────────
        async def local_storage_demo(page):
            await page.goto("https://example.com")
            await set_local_storage(page, {"kryptic": "hello", "version": "0.2.0"})
            storage = await get_local_storage(page)
            return storage

        storage = await k.run(local_storage_demo)
        print(f"\nlocalStorage: {storage}")

        # ── 4. Full storage state ────────────────────────────────────────────
        async def save_full_state(page):
            await page.goto("https://httpbin.org/cookies/set/fullstate/yes")
            state = await save_storage_state(page, STATE_FILE)
            return len(state.get("cookies", []))

        num_cookies = await k.run(save_full_state)
        print(f"\nFull state saved: {num_cookies} cookies → {STATE_FILE}")

        # Cleanup
        for f in [COOKIE_FILE, STATE_FILE]:
            if os.path.exists(f):
                os.remove(f)


asyncio.run(main())
