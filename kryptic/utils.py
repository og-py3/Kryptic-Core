import asyncio
from typing import Optional
from .types import BrowserTypeName, BrowserInfo


async def detect_browsers() -> list[BrowserInfo]:
    """
    Check which Playwright browsers are installed and available.
    Returns a list of BrowserInfo dicts with name and availability.
    """
    from playwright.async_api import async_playwright

    results: list[BrowserInfo] = []
    browser_types: list[BrowserTypeName] = ["chromium", "firefox", "webkit"]

    async with async_playwright() as p:
        for name in browser_types:
            try:
                bt = getattr(p, name)
                browser = await bt.launch(headless=True, timeout=10_000)
                await browser.close()
                results.append({"name": name, "available": True})
            except Exception:
                results.append({"name": name, "available": False})

    return results


def available_browser_names() -> list[BrowserTypeName]:
    """
    Synchronous helper — run detect_browsers() and return only the names
    of browsers that launched successfully.
    """
    infos = asyncio.run(detect_browsers())
    return [info["name"] for info in infos if info["available"]]


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.2f}s"
