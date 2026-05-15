"""
Stealth profiles — reduce bot-detection signals.

Usage:
    from kryptic.stealth import StealthProfile

    profile = StealthProfile(level="high")

    async def task(page):
        await profile.apply(page)
        await page.goto("https://example.com")
        ...
"""
import random
from typing import Optional

from .context import PageContext

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 800},
    {"width": 2560, "height": 1440},
]

LOCALES = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ja-JP"]
TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Los_Angeles",
    "Europe/London", "Europe/Berlin", "Europe/Paris",
    "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney",
]

# JavaScript injected to mask automation signals
_STEALTH_JS = """
() => {
    // Remove webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Fake plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // Fake languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });

    // Mask Chrome automation
    window.chrome = { runtime: {} };

    // Permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);

    // Remove automation-specific properties
    delete window.__selenium_unwrapped;
    delete window.__webdriver_evaluate;
    delete window.__driver_evaluate;
    delete window.__webdriver_script_func;
    delete window.callPhantom;
    delete window._phantom;
    delete window.phantom;
    delete window.__nightmare;
    delete window.domAutomation;
    delete window.domAutomationController;
}
"""


class StealthProfile:
    """
    A randomised browser fingerprint profile.

    Levels:
      "low"    — just randomise User-Agent
      "medium" — random UA, viewport, locale, timezone (default)
      "high"   — everything + inject anti-detection JS
    """

    def __init__(
        self,
        level: str = "medium",
        user_agent: Optional[str] = None,
        locale: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> None:
        if level not in ("low", "medium", "high"):
            raise ValueError("level must be 'low', 'medium', or 'high'")
        self.level = level
        self.user_agent = user_agent or random.choice(USER_AGENTS)
        self.locale = locale or random.choice(LOCALES)
        self.timezone = timezone or random.choice(TIMEZONES)
        self.viewport = random.choice(VIEWPORTS)

    def random_user_agent(self) -> str:
        self.user_agent = random.choice(USER_AGENTS)
        return self.user_agent

    async def apply(self, page: PageContext) -> None:
        """Apply this stealth profile to a PageContext."""
        if self.level in ("low", "medium", "high"):
            await page.set_headers({"User-Agent": self.user_agent})

        if self.level in ("medium", "high"):
            await page.raw.set_viewport_size(self.viewport)

        if self.level == "high":
            await page.raw.add_init_script(_STEALTH_JS)

    def context_options(self) -> dict:
        """
        Return options to pass to browser.new_context() for full stealth.
        Use this when creating the browser context, not after.
        """
        opts: dict = {
            "user_agent": self.user_agent,
            "locale": self.locale,
            "timezone_id": self.timezone,
            "viewport": self.viewport,
            "color_scheme": random.choice(["light", "dark"]),
            "device_scale_factor": random.choice([1, 1, 1, 1.5, 2]),
        }
        return opts

    def __repr__(self) -> str:
        return (
            f"StealthProfile(level={self.level!r}, "
            f"ua={self.user_agent[:40]!r}..., "
            f"viewport={self.viewport})"
        )


def random_profile(level: str = "medium") -> StealthProfile:
    """Convenience factory — returns a freshly randomised StealthProfile."""
    return StealthProfile(level=level)
