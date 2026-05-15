import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Playwright

from .types import BrowserTypeName


class BrowserPool:
    """
    Manages a pool of browser instances distributed across one or more
    browser types. Tasks are dispatched to the first available browser,
    enabling true parallel execution.
    """

    def __init__(
        self,
        concurrency: int,
        headless: bool,
        browser_types: list[BrowserTypeName],
        timeout: int = 30_000,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self._concurrency = concurrency
        self._headless = headless
        self._browser_types = browser_types
        self._timeout = timeout
        self._user_agent = user_agent
        self._proxy = proxy

        self._playwright: Optional[Playwright] = None
        self._browsers: list[Browser] = []
        self._queue: asyncio.Queue[Browser] = asyncio.Queue()

    async def init(self) -> None:
        self._playwright = await async_playwright().start()

        launch_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-translate",
            "--no-first-run",
        ]

        proxy_config = {"server": self._proxy} if self._proxy else None

        for i in range(self._concurrency):
            type_name = self._browser_types[i % len(self._browser_types)]
            bt = getattr(self._playwright, type_name)

            kwargs: dict = {
                "headless": self._headless,
                "timeout": self._timeout,
            }
            if type_name == "chromium":
                kwargs["args"] = launch_args
            if proxy_config:
                kwargs["proxy"] = proxy_config

            browser = await bt.launch(**kwargs)
            self._browsers.append(browser)
            await self._queue.put(browser)

    async def acquire(self) -> Browser:
        """Block until a browser instance is free, then return it."""
        return await self._queue.get()

    async def release(self, browser: Browser) -> None:
        """Return a browser instance back to the pool."""
        await self._queue.put(browser)

    async def close(self) -> None:
        for browser in self._browsers:
            try:
                await browser.close()
            except Exception:
                pass
        if self._playwright:
            await self._playwright.stop()

    @property
    def size(self) -> int:
        return len(self._browsers)

    @property
    def available(self) -> int:
        return self._queue.qsize()
