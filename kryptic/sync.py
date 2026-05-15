"""
Synchronous wrapper — use Kryptic without asyncio.

    from kryptic.sync import KrypticSync

    with KrypticSync(concurrency=4) as k:
        title = k.run(lambda page: page.goto("https://example.com") or page.title())
        results = k.batch([lambda page: page.goto(url) or page.title() for url in urls])
"""
import asyncio
import threading
from typing import Any, Callable, Optional

from .core import Kryptic
from .types import BrowserTypeName, Mode


class KrypticSync:
    """
    Synchronous, blocking wrapper around Kryptic.

    Spins up a dedicated event loop in a background thread so you can call
    .run() and .batch() without writing any async code.
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
        self._kwargs = dict(
            mode=mode,
            headless=headless,
            concurrency=concurrency,
            browser_types=browser_types,
            timeout=timeout,
            user_agent=user_agent,
            proxy=proxy,
        )
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._kryptic: Optional[Kryptic] = None

    def _start_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._loop.run_forever()

    def _call(self, coro: Any) -> Any:
        assert self._loop is not None
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result()

    def start(self) -> "KrypticSync":
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()
        while self._loop is None:
            pass
        self._kryptic = Kryptic(**self._kwargs)
        self._call(self._kryptic.init())
        return self

    def stop(self) -> None:
        if self._kryptic:
            self._call(self._kryptic.close())
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def __enter__(self) -> "KrypticSync":
        return self.start()

    def __exit__(self, *_: Any) -> None:
        self.stop()

    def run(self, task: Callable) -> Any:
        """
        Run a single task synchronously.

        task can be:
          - an async def function (receives PageContext or HttpClient)
          - a sync lambda that returns an awaitable (the result is awaited for you)

        Example:
            result = k.run(lambda page: page.goto("https://x.com") or page.title())
            # Note: since page.goto returns None, `or page.title()` evaluates the
            # coroutine — pass a proper async def for complex tasks.
        """
        assert self._kryptic is not None
        import inspect

        async def _wrap(ctx: Any) -> Any:
            result = task(ctx)
            if inspect.isawaitable(result):
                return await result
            return result

        return self._call(self._kryptic.run(_wrap))

    def batch(self, tasks: list[Callable]) -> list[Any]:
        assert self._kryptic is not None
        import inspect

        async def _wrap(task: Callable, ctx: Any) -> Any:
            result = task(ctx)
            if inspect.isawaitable(result):
                return await result
            return result

        return self._call(
            self._kryptic.batch([
                (lambda t: lambda ctx: _wrap(t, ctx))(task)
                for task in tasks
            ])
        )

    def batch_timed(self, tasks: list[Callable]) -> dict[str, Any]:
        assert self._kryptic is not None
        import inspect

        async def _wrap(task: Callable, ctx: Any) -> Any:
            result = task(ctx)
            if inspect.isawaitable(result):
                return await result
            return result

        return self._call(
            self._kryptic.batch_timed([
                (lambda t: lambda ctx: _wrap(t, ctx))(task)
                for task in tasks
            ])
        )

    def http_get(self, url: str, **kwargs: Any) -> Any:
        return self.run(lambda http: http.get(url, **kwargs))

    def http_post(self, url: str, **kwargs: Any) -> Any:
        return self.run(lambda http: http.post(url, **kwargs))

    def __repr__(self) -> str:
        return f"KrypticSync({self._kwargs})"
