import asyncio
import time
from typing import Any, Callable, Coroutine, Literal, Optional

from .pool import BrowserPool
from .context import PageContext
from .http_client import HttpClient
from .types import BrowserTypeName, Mode


class Kryptic:
    """
    Fast, concurrent browser automation library.

    Two modes:
      - 'browser'  — pool of real headless browsers (Playwright)
      - 'http'     — pure HTTP/S requests, zero browser overhead

    Usage (context manager — recommended):

        async with Kryptic(concurrency=4) as k:
            title = await k.run(lambda page: page.goto("https://example.com") or page.title())

        async with Kryptic(mode="http", concurrency=20) as k:
            resp = await k.run(lambda http: http.get("https://example.com"))

    Usage (manual init):

        k = Kryptic(concurrency=4)
        await k.init()
        ...
        await k.close()
    """

    def __init__(
        self,
        mode: Mode = "browser",
        headless: bool = True,
        concurrency: int = 4,
        browser_types: Optional[list[BrowserTypeName]] = None,
        timeout: int = 30_000,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self._mode = mode
        self._headless = headless
        self._concurrency = concurrency
        self._browser_types: list[BrowserTypeName] = browser_types or ["chromium"]
        self._timeout = timeout
        self._user_agent = user_agent
        self._proxy = proxy

        self._pool: Optional[BrowserPool] = None
        self._http_client: Optional[HttpClient] = None
        self._ready = False

    async def init(self) -> None:
        """Initialise the browser pool or HTTP client."""
        if self._mode == "browser":
            self._pool = BrowserPool(
                concurrency=self._concurrency,
                headless=self._headless,
                browser_types=self._browser_types,
                timeout=self._timeout,
                user_agent=self._user_agent,
                proxy=self._proxy,
            )
            await self._pool.init()
        else:
            self._http_client = HttpClient(
                concurrency=self._concurrency,
                timeout=self._timeout // 1000,
                user_agent=self._user_agent,
                proxy=self._proxy,
            )
            await self._http_client.init()

        self._ready = True

    def _check_ready(self) -> None:
        if not self._ready:
            raise RuntimeError(
                "Kryptic is not initialised. "
                "Use `async with Kryptic(...) as k:` or call `await k.init()` first."
            )

    async def run(
        self,
        task: Callable[[Any], Coroutine[Any, Any, Any]],
    ) -> Any:
        """
        Run a single task.

        In browser mode:  task receives a PageContext  (page.goto, page.text, …)
        In http mode:     task receives an HttpClient  (http.get, http.post, …)
        """
        self._check_ready()

        if self._mode == "browser":
            assert self._pool is not None
            browser = await self._pool.acquire()
            try:
                context = await browser.new_context(
                    user_agent=self._user_agent or None,
                    proxy={"server": self._proxy} if self._proxy else None,
                )
                page = await context.new_page()
                ctx = PageContext(page, timeout=self._timeout)
                result = await task(ctx)
                await context.close()
                return result
            finally:
                await self._pool.release(browser)
        else:
            assert self._http_client is not None
            return await task(self._http_client)

    async def batch(
        self,
        tasks: list[Callable[[Any], Coroutine[Any, Any, Any]]],
    ) -> list[Any]:
        """
        Run multiple tasks concurrently.
        All tasks are dispatched at once; the pool caps how many run in parallel.
        Returns results in the same order as the input tasks.
        """
        self._check_ready()
        return list(await asyncio.gather(*[self.run(t) for t in tasks]))

    async def batch_timed(
        self,
        tasks: list[Callable[[Any], Coroutine[Any, Any, Any]]],
    ) -> dict[str, Any]:
        """
        Like batch(), but also returns wall-clock timing info.

        Returns:
            {
                "results": [...],
                "total_seconds": float,
                "tasks": int,
                "avg_seconds": float,
            }
        """
        start = time.perf_counter()
        results = await self.batch(tasks)
        elapsed = time.perf_counter() - start
        return {
            "results": results,
            "total_seconds": round(elapsed, 3),
            "tasks": len(tasks),
            "avg_seconds": round(elapsed / max(len(tasks), 1), 3),
        }

    async def close(self) -> None:
        """Shut down all browsers / HTTP connections."""
        if self._pool:
            await self._pool.close()
        if self._http_client:
            await self._http_client.close()
        self._ready = False

    async def __aenter__(self) -> "Kryptic":
        await self.init()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def concurrency(self) -> int:
        return self._concurrency

    @property
    def pool_size(self) -> int:
        return self._pool.size if self._pool else 0

    @property
    def available_slots(self) -> int:
        return self._pool.available if self._pool else self._concurrency

    def __repr__(self) -> str:
        return (
            f"Kryptic(mode={self._mode!r}, concurrency={self._concurrency}, "
            f"headless={self._headless}, browsers={self._browser_types})"
        )
