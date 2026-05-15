"""
Cookie and browser storage persistence — save/restore sessions across runs.

    from kryptic.storage import save_cookies, load_cookies, save_storage_state, load_storage_state

    # Save after login
    async with Kryptic() as k:
        async def login(page):
            await page.goto("https://example.com/login")
            await page.fill("#email", "user@example.com")
            await page.fill("#password", "secret")
            await page.click("[type=submit]")
            await page.wait_for_load()
            await save_cookies(page, "session.json")
        await k.run(login)

    # Restore in a new session
    async with Kryptic() as k:
        async def use_session(page):
            await load_cookies(page, "session.json")
            await page.goto("https://example.com/dashboard")
            return await page.title()
        print(await k.run(use_session))
"""
import json
import os
from typing import Any, Optional

from .context import PageContext


async def save_cookies(page: PageContext, path: str) -> list[dict]:
    """Save the current page's cookies to a JSON file. Returns the cookie list."""
    cookies = await page.cookies()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    return cookies


async def load_cookies(page: PageContext, path: str) -> None:
    """Load cookies from a JSON file into the page's browser context."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cookie file not found: {path}")
    with open(path, encoding="utf-8") as f:
        cookies = json.load(f)
    await page.set_cookies(cookies)


async def save_storage_state(page: PageContext, path: str) -> dict[str, Any]:
    """
    Save full browser storage state (cookies + localStorage + sessionStorage).
    Returns the state dict.
    """
    state = await page.raw.context.storage_state()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return state


def load_storage_state(path: str) -> dict[str, Any]:
    """
    Load storage state from a JSON file.

    Pass the returned dict as `storage_state` to browser.new_context():

        state = load_storage_state("session.json")
        ctx = await browser.new_context(storage_state=state)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Storage state file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def get_local_storage(page: PageContext) -> dict[str, str]:
    """Return the page's localStorage as a Python dict."""
    return await page.evaluate("""
        () => Object.fromEntries(
            Object.keys(localStorage).map(k => [k, localStorage.getItem(k)])
        )
    """)


async def set_local_storage(page: PageContext, data: dict[str, str]) -> None:
    """Set localStorage key/value pairs."""
    for key, value in data.items():
        await page.evaluate(
            f"([k, v]) => localStorage.setItem(k, v)",
            [key, value],
        )


async def clear_local_storage(page: PageContext) -> None:
    await page.evaluate("() => localStorage.clear()")


async def get_session_storage(page: PageContext) -> dict[str, str]:
    return await page.evaluate("""
        () => Object.fromEntries(
            Object.keys(sessionStorage).map(k => [k, sessionStorage.getItem(k)])
        )
    """)
