import asyncio
from typing import Any, Callable, Optional
from playwright.async_api import Page, ElementHandle, Route, Request


class Element:
    """Wrapper around a Playwright ElementHandle with a cleaner API."""

    def __init__(self, handle: ElementHandle) -> None:
        self._handle = handle

    async def text(self) -> str:
        return await self._handle.inner_text()

    async def html(self) -> str:
        return await self._handle.inner_html()

    async def attr(self, name: str) -> Optional[str]:
        return await self._handle.get_attribute(name)

    async def click(self) -> None:
        await self._handle.click()

    async def fill(self, value: str) -> None:
        await self._handle.fill(value)

    async def is_visible(self) -> bool:
        return await self._handle.is_visible()

    async def is_enabled(self) -> bool:
        return await self._handle.is_enabled()

    async def bounding_box(self) -> Optional[dict[str, float]]:
        return await self._handle.bounding_box()

    async def scroll_into_view(self) -> None:
        await self._handle.scroll_into_view_if_needed()

    async def select_text(self) -> None:
        await self._handle.select_text()

    async def focus(self) -> None:
        await self._handle.focus()

    @property
    def raw(self) -> ElementHandle:
        return self._handle


class PageContext:
    """
    High-level, fast page automation context wrapping a Playwright Page.
    Uses domcontentloaded by default for maximum speed.
    """

    def __init__(self, page: Page, timeout: int = 30_000) -> None:
        self._page = page
        self._default_timeout = timeout
        self._page.set_default_timeout(timeout)

    # ── Navigation ─────────────────────────────────────────────────────────────

    async def goto(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: Optional[int] = None,
    ) -> None:
        await self._page.goto(
            url, wait_until=wait_until, timeout=timeout or self._default_timeout
        )

    async def reload(self, wait_until: str = "domcontentloaded") -> None:
        await self._page.reload(wait_until=wait_until)

    async def go_back(self) -> None:
        await self._page.go_back()

    async def go_forward(self) -> None:
        await self._page.go_forward()

    async def title(self) -> str:
        return await self._page.title()

    async def html(self) -> str:
        return await self._page.content()

    @property
    def url(self) -> str:
        return self._page.url

    # ── Interactions ───────────────────────────────────────────────────────────

    async def click(self, selector: str, timeout: Optional[int] = None) -> None:
        await self._page.click(selector, timeout=timeout or self._default_timeout)

    async def double_click(self, selector: str) -> None:
        await self._page.dbl_click(selector)

    async def right_click(self, selector: str) -> None:
        await self._page.click(selector, button="right")

    async def fill(self, selector: str, value: str) -> None:
        await self._page.fill(selector, value)

    async def type_slowly(self, selector: str, text: str, delay: int = 50) -> None:
        await self._page.type(selector, text, delay=delay)

    async def clear(self, selector: str) -> None:
        await self._page.fill(selector, "")

    async def select(self, selector: str, value: str) -> None:
        await self._page.select_option(selector, value)

    async def press(self, selector: str, key: str) -> None:
        await self._page.press(selector, key)

    async def hover(self, selector: str) -> None:
        await self._page.hover(selector)

    async def focus(self, selector: str) -> None:
        await self._page.focus(selector)

    async def tap(self, selector: str) -> None:
        await self._page.tap(selector)

    async def drag_and_drop(self, source: str, target: str) -> None:
        await self._page.drag_and_drop(source, target)

    async def upload_file(self, selector: str, *paths: str) -> None:
        """Upload one or more files to a file input."""
        await self._page.set_input_files(selector, list(paths))

    async def check(self, selector: str) -> None:
        await self._page.check(selector)

    async def uncheck(self, selector: str) -> None:
        await self._page.uncheck(selector)

    async def is_checked(self, selector: str) -> bool:
        return await self._page.is_checked(selector)

    # ── Querying ───────────────────────────────────────────────────────────────

    async def text(self, selector: str) -> str:
        return await self._page.inner_text(selector)

    async def attr(self, selector: str, name: str) -> Optional[str]:
        return await self._page.get_attribute(selector, name)

    async def input_value(self, selector: str) -> str:
        return await self._page.input_value(selector)

    async def find(self, selector: str) -> list[Element]:
        handles = await self._page.query_selector_all(selector)
        return [Element(h) for h in handles]

    async def find_one(self, selector: str) -> Optional[Element]:
        handle = await self._page.query_selector(selector)
        return Element(handle) if handle else None

    async def count(self, selector: str) -> int:
        return await self._page.locator(selector).count()

    async def exists(self, selector: str) -> bool:
        return (await self._page.query_selector(selector)) is not None

    async def is_visible(self, selector: str) -> bool:
        return await self._page.is_visible(selector)

    # ── Waiting ────────────────────────────────────────────────────────────────

    async def wait_for(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None,
    ) -> Element:
        handle = await self._page.wait_for_selector(
            selector, state=state, timeout=timeout or self._default_timeout
        )
        if handle is None:
            raise TimeoutError(f"Selector '{selector}' not found")
        return Element(handle)

    async def wait_for_url(self, url_pattern: str, timeout: Optional[int] = None) -> None:
        await self._page.wait_for_url(
            url_pattern, timeout=timeout or self._default_timeout
        )

    async def wait_for_load(
        self, state: str = "networkidle", timeout: Optional[int] = None
    ) -> None:
        await self._page.wait_for_load_state(
            state, timeout=timeout or self._default_timeout
        )

    async def wait_for_response(
        self, url_pattern: str, timeout: Optional[int] = None
    ) -> Any:
        return await self._page.wait_for_response(
            url_pattern, timeout=timeout or self._default_timeout
        )

    async def wait_for_navigation(self, timeout: Optional[int] = None) -> None:
        async with self._page.expect_navigation(
            timeout=timeout or self._default_timeout
        ):
            pass

    # ── JavaScript ─────────────────────────────────────────────────────────────

    async def evaluate(self, js: str, *args: Any) -> Any:
        return await self._page.evaluate(js, *args)

    async def evaluate_on(self, selector: str, js: str) -> Any:
        return await self._page.eval_on_selector(selector, js)

    async def add_script_tag(self, url: Optional[str] = None, content: Optional[str] = None) -> None:
        await self._page.add_script_tag(url=url, content=content)

    async def add_style_tag(self, url: Optional[str] = None, content: Optional[str] = None) -> None:
        await self._page.add_style_tag(url=url, content=content)

    # ── Screenshots & PDF ──────────────────────────────────────────────────────

    async def screenshot(self, path: str, full_page: bool = False) -> bytes:
        return await self._page.screenshot(path=path, full_page=full_page)

    async def screenshot_bytes(self, full_page: bool = False) -> bytes:
        return await self._page.screenshot(full_page=full_page)

    async def screenshot_element(self, selector: str, path: Optional[str] = None) -> bytes:
        """Screenshot a specific element only."""
        locator = self._page.locator(selector)
        return await locator.screenshot(path=path)

    async def pdf(
        self,
        path: Optional[str] = None,
        format: str = "A4",
        print_background: bool = True,
        margin: Optional[dict] = None,
    ) -> bytes:
        """
        Generate a PDF of the page (Chromium only).

        Returns the PDF bytes; also saves to path if provided.
        """
        kwargs: dict = {
            "format": format,
            "print_background": print_background,
        }
        if path:
            kwargs["path"] = path
        if margin:
            kwargs["margin"] = margin
        return await self._page.pdf(**kwargs)

    # ── Network ────────────────────────────────────────────────────────────────

    async def intercept(
        self,
        url_pattern: str,
        handler: Callable[[Route, Request], Any],
    ) -> None:
        await self._page.route(url_pattern, handler)

    async def block_resources(self, resource_types: list[str]) -> None:
        """Block resource types (image, stylesheet, font, media, script, etc.)."""
        async def _abort(route: Route, req: Request) -> None:
            if req.resource_type in resource_types:
                await route.abort()
            else:
                await route.continue_()
        await self._page.route("**/*", _abort)

    async def block_ads(self) -> None:
        """Block common ad/tracker domains for faster scraping."""
        patterns = [
            "*googlesyndication*", "*doubleclick*", "*google-analytics*",
            "*googletagmanager*", "*facebook.net*", "*amazon-adsystem*",
            "*hotjar*", "*mixpanel*", "*segment.com*",
        ]
        for p in patterns:
            await self._page.route(p, lambda route, _: route.abort())

    async def set_headers(self, headers: dict[str, str]) -> None:
        await self._page.set_extra_http_headers(headers)

    # ── Cookies & Storage ──────────────────────────────────────────────────────

    async def cookies(self) -> list[dict]:
        return await self._page.context.cookies()

    async def set_cookies(self, cookies: list[dict]) -> None:
        await self._page.context.add_cookies(cookies)

    async def clear_cookies(self) -> None:
        await self._page.context.clear_cookies()

    # ── Dialogs ────────────────────────────────────────────────────────────────

    def on_dialog(self, handler: Callable) -> None:
        """
        Handle browser dialogs (alert, confirm, prompt).

        handler(dialog) — call await dialog.accept() or await dialog.dismiss().

        Example:
            page.on_dialog(lambda d: d.accept())
        """
        self._page.on("dialog", handler)

    def auto_accept_dialogs(self) -> None:
        """Auto-accept all dialogs (alert, confirm, prompt)."""
        async def _accept(dialog: Any) -> None:
            await dialog.accept()
        self._page.on("dialog", _accept)

    def auto_dismiss_dialogs(self) -> None:
        """Auto-dismiss all dialogs."""
        async def _dismiss(dialog: Any) -> None:
            await dialog.dismiss()
        self._page.on("dialog", _dismiss)

    # ── Frames / iFrames ───────────────────────────────────────────────────────

    async def frame(self, selector: str) -> Optional["PageContext"]:
        """
        Return a PageContext wrapping an iframe's content frame.

        Example:
            iframe_ctx = await page.frame("iframe#widget")
            text = await iframe_ctx.text("h1")
        """
        element = await self._page.query_selector(selector)
        if element is None:
            return None
        frame = await element.content_frame()
        if frame is None:
            return None
        return PageContext(frame, timeout=self._default_timeout)  # type: ignore[arg-type]

    def frames(self) -> list[Any]:
        """Return all frames on the page."""
        return self._page.frames

    # ── Scrolling ──────────────────────────────────────────────────────────────

    async def scroll_to_bottom(self) -> None:
        await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def scroll_to(self, x: int = 0, y: int = 0) -> None:
        await self._page.evaluate(f"window.scrollTo({x}, {y})")

    async def scroll_by(self, x: int = 0, y: int = 0) -> None:
        await self._page.evaluate(f"window.scrollBy({x}, {y})")

    async def scroll_into_view(self, selector: str) -> None:
        el = await self._page.query_selector(selector)
        if el:
            await el.scroll_into_view_if_needed()

    async def infinite_scroll(
        self,
        max_scrolls: int = 20,
        pause: float = 0.8,
        selector: Optional[str] = None,
    ) -> int:
        """
        Scroll to the bottom repeatedly to trigger infinite scroll loading.

        Returns the number of scrolls performed.
        Stops early if:
          - the page height stops growing (content loaded)
          - max_scrolls is reached
          - selector is given and no longer found (end-of-content marker)
        """
        prev_height = 0
        for i in range(max_scrolls):
            height: int = await self._page.evaluate(
                "() => document.body.scrollHeight"
            )
            if height == prev_height:
                return i
            if selector and not await self.exists(selector):
                return i
            await self.scroll_to_bottom()
            await asyncio.sleep(pause)
            prev_height = height
        return max_scrolls

    # ── Keyboard ───────────────────────────────────────────────────────────────

    async def key(self, key: str) -> None:
        """Press a keyboard key globally (e.g. "Enter", "Escape", "Tab")."""
        await self._page.keyboard.press(key)

    async def key_down(self, key: str) -> None:
        await self._page.keyboard.down(key)

    async def key_up(self, key: str) -> None:
        await self._page.keyboard.up(key)

    # ── Viewport & Device ──────────────────────────────────────────────────────

    async def emulate_device(self, device_name: str) -> None:
        """Apply a mobile device profile (from kryptic.mobile.DEVICES)."""
        from .mobile import get_device
        d = get_device(device_name)
        await self._page.set_viewport_size(d["viewport"])
        await self.set_headers({"User-Agent": d["user_agent"]})

    # ── Performance & Metrics ──────────────────────────────────────────────────

    async def metrics(self) -> dict[str, float]:
        """Return Chromium performance metrics (timing, memory, etc.)."""
        raw = await self._page.evaluate("""
            () => {
                const nav = performance.getEntriesByType('navigation')[0] || {};
                const paint = Object.fromEntries(
                    performance.getEntriesByType('paint').map(e => [e.name, e.startTime])
                );
                return {
                    dns: (nav.domainLookupEnd || 0) - (nav.domainLookupStart || 0),
                    tcp: (nav.connectEnd || 0) - (nav.connectStart || 0),
                    ttfb: (nav.responseStart || 0) - (nav.requestStart || 0),
                    dom_content_loaded: nav.domContentLoadedEventEnd || 0,
                    load: nav.loadEventEnd || 0,
                    first_paint: paint['first-paint'] || 0,
                    first_contentful_paint: paint['first-contentful-paint'] || 0,
                };
            }
        """)
        return raw

    async def accessibility_tree(self) -> dict:
        """Return the accessibility tree snapshot."""
        return await self._page.accessibility.snapshot() or {}

    # ── Misc ───────────────────────────────────────────────────────────────────

    async def set_viewport(self, width: int, height: int) -> None:
        """Resize the browser viewport."""
        await self._page.set_viewport_size({"width": width, "height": height})

    @property
    def raw(self) -> Page:
        """Access the underlying Playwright Page for advanced use."""
        return self._page
