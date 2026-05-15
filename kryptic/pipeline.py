"""
Browser automation pipeline — build multi-step flows with a chainable API.

    from kryptic import Kryptic
    from kryptic.pipeline import Pipeline

    async with Kryptic() as k:
        result = await (
            Pipeline(k)
            .goto("https://example.com")
            .block(["image", "stylesheet"])
            .wait_for("h1")
            .extract("heading", "h1")
            .extract("title", "title", method="title")
            .screenshot("out.png")
            .run()
        )
        print(result)  # {"heading": "Example Domain", "title": "Example Domain"}
"""
import asyncio
from typing import Any, Callable, Optional

from .core import Kryptic
from .context import PageContext


class _Step:
    def __init__(self, name: str, fn: Callable) -> None:
        self.name = name
        self.fn = fn


class Pipeline:
    """
    Chainable multi-step browser automation pipeline.

    Each step is queued; calling .run() executes them in order on a single
    browser session and returns a dict of all extracted values.
    """

    def __init__(self, kryptic: Kryptic) -> None:
        self._kryptic = kryptic
        self._steps: list[_Step] = []
        self._results: dict[str, Any] = {}

    # ── Navigation ─────────────────────────────────────────────────────────────

    def goto(self, url: str, wait_until: str = "domcontentloaded") -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.goto(url, wait_until=wait_until)
        return self._add("goto", _step)

    def reload(self) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.reload()
        return self._add("reload", _step)

    def go_back(self) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.go_back()
        return self._add("go_back", _step)

    # ── Interactions ───────────────────────────────────────────────────────────

    def click(self, selector: str) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.click(selector)
        return self._add(f"click({selector})", _step)

    def fill(self, selector: str, value: str) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.fill(selector, value)
        return self._add(f"fill({selector})", _step)

    def press(self, selector: str, key: str) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.press(selector, key)
        return self._add(f"press({key})", _step)

    def select(self, selector: str, value: str) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.select(selector, value)
        return self._add(f"select({selector}={value})", _step)

    def hover(self, selector: str) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.hover(selector)
        return self._add(f"hover({selector})", _step)

    # ── Speed helpers ──────────────────────────────────────────────────────────

    def block(self, resource_types: list[str]) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.block_resources(resource_types)
        return self._add("block_resources", _step)

    def block_ads(self) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.block_ads()
        return self._add("block_ads", _step)

    # ── Waiting ────────────────────────────────────────────────────────────────

    def wait_for(self, selector: str, state: str = "visible") -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.wait_for(selector, state=state)
        return self._add(f"wait_for({selector})", _step)

    def wait_for_load(self, state: str = "networkidle") -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.wait_for_load(state)
        return self._add(f"wait_for_load({state})", _step)

    def sleep(self, seconds: float) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await asyncio.sleep(seconds)
        return self._add(f"sleep({seconds})", _step)

    # ── Extraction ─────────────────────────────────────────────────────────────

    def extract(
        self,
        key: str,
        selector: str,
        method: str = "text",
        attribute: Optional[str] = None,
    ) -> "Pipeline":
        """
        Extract a value and store it under key in the results dict.

        method:
          "text"      — inner text of the selector
          "html"      — outer HTML
          "attr"      — attribute value (requires attribute= kwarg)
          "title"     — page title (selector ignored)
          "url"       — current URL (selector ignored)
          "count"     — number of matching elements
        """
        async def _step(page: PageContext, results: dict) -> None:
            if method == "text":
                results[key] = await page.text(selector)
            elif method == "html":
                results[key] = await page.html()
            elif method == "attr" and attribute:
                results[key] = await page.attr(selector, attribute)
            elif method == "title":
                results[key] = await page.title()
            elif method == "url":
                results[key] = page.url
            elif method == "count":
                elements = await page.find(selector)
                results[key] = len(elements)
            else:
                results[key] = await page.text(selector)
        return self._add(f"extract({key})", _step)

    def extract_all(self, key: str, selector: str) -> "Pipeline":
        """Extract the inner text of all matching elements as a list."""
        async def _step(page: PageContext, results: dict) -> None:
            elements = await page.find(selector)
            results[key] = [await el.text() for el in elements]
        return self._add(f"extract_all({key})", _step)

    def evaluate(self, key: str, js: str) -> "Pipeline":
        """Run JavaScript and store the result."""
        async def _step(page: PageContext, results: dict) -> None:
            results[key] = await page.evaluate(js)
        return self._add(f"evaluate({key})", _step)

    # ── Side effects ───────────────────────────────────────────────────────────

    def screenshot(self, path: str, full_page: bool = False) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.screenshot(path, full_page=full_page)
        return self._add(f"screenshot({path})", _step)

    def scroll_to_bottom(self) -> "Pipeline":
        async def _step(page: PageContext, _: dict) -> None:
            await page.scroll_to_bottom()
        return self._add("scroll_to_bottom", _step)

    def custom(self, name: str, fn: Callable[[PageContext, dict], Any]) -> "Pipeline":
        """Add a custom async step: fn(page, results) -> None."""
        return self._add(name, fn)

    # ── Execution ──────────────────────────────────────────────────────────────

    def _add(self, name: str, fn: Callable) -> "Pipeline":
        self._steps.append(_Step(name, fn))
        return self

    async def run(self) -> dict[str, Any]:
        """Execute all queued steps and return the extracted results dict."""
        results: dict[str, Any] = {}

        async def _execute(page: PageContext) -> dict:
            for step in self._steps:
                await step.fn(page, results)
            return results

        await self._kryptic.run(_execute)
        return results

    def __repr__(self) -> str:
        steps = " → ".join(s.name for s in self._steps)
        return f"Pipeline([{steps}])"
