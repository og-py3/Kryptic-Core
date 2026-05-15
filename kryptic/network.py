"""
Network monitoring — capture, filter, and inspect all browser requests/responses.

    from kryptic.network import NetworkMonitor

    async def task(page):
        monitor = NetworkMonitor(page)
        await monitor.start()
        await page.goto("https://example.com")
        log = monitor.log

        # Filter
        api_calls = monitor.filter(resource_type="fetch")
        images    = monitor.filter(resource_type="image")
        slow      = monitor.slow_requests(threshold_ms=500)

        return log
"""
import asyncio
import time
from typing import Any, Callable, Optional

from .context import PageContext


class NetworkEntry:
    """A single captured request/response pair."""

    def __init__(self, request: Any) -> None:
        self.url: str = request.url
        self.method: str = request.method
        self.resource_type: str = request.resource_type
        self.headers: dict[str, str] = dict(request.headers)
        self.start_time: float = time.monotonic()
        self.end_time: Optional[float] = None
        self.status: Optional[int] = None
        self.response_headers: dict[str, str] = {}
        self.response_size: int = 0
        self.failed: bool = False
        self.failure_reason: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return round((self.end_time - self.start_time) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "resource_type": self.resource_type,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "response_size": self.response_size,
            "failed": self.failed,
            "failure_reason": self.failure_reason,
        }

    def __repr__(self) -> str:
        return (
            f"NetworkEntry({self.method} {self.url[:60]} "
            f"→ {self.status}, {self.duration_ms}ms)"
        )


class NetworkMonitor:
    """
    Attach to a PageContext and record all requests and responses.
    """

    def __init__(self, page: PageContext) -> None:
        self._page = page
        self._log: list[NetworkEntry] = []
        self._pending: dict[str, NetworkEntry] = {}

    async def start(self) -> None:
        """Start recording network traffic."""
        self._page.raw.on("request", self._on_request)
        self._page.raw.on("response", self._on_response)
        self._page.raw.on("requestfailed", self._on_failed)

    def stop(self) -> None:
        """Stop recording (removes event listeners)."""
        try:
            self._page.raw.remove_listener("request", self._on_request)
            self._page.raw.remove_listener("response", self._on_response)
            self._page.raw.remove_listener("requestfailed", self._on_failed)
        except Exception:
            pass

    def _on_request(self, request: Any) -> None:
        entry = NetworkEntry(request)
        self._pending[request.url] = entry
        self._log.append(entry)

    def _on_response(self, response: Any) -> None:
        entry = self._pending.pop(response.request.url, None)
        if entry:
            entry.end_time = time.monotonic()
            entry.status = response.status
            entry.response_headers = dict(response.headers)

    def _on_failed(self, request: Any) -> None:
        entry = self._pending.pop(request.url, None)
        if entry:
            entry.end_time = time.monotonic()
            entry.failed = True
            entry.failure_reason = request.failure

    @property
    def log(self) -> list[NetworkEntry]:
        return list(self._log)

    def filter(
        self,
        resource_type: Optional[str] = None,
        method: Optional[str] = None,
        url_contains: Optional[str] = None,
        status: Optional[int] = None,
        failed: Optional[bool] = None,
    ) -> list[NetworkEntry]:
        """Filter the network log by any combination of attributes."""
        results = self._log
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if method:
            results = [e for e in results if e.method.upper() == method.upper()]
        if url_contains:
            results = [e for e in results if url_contains in e.url]
        if status is not None:
            results = [e for e in results if e.status == status]
        if failed is not None:
            results = [e for e in results if e.failed == failed]
        return results

    def slow_requests(self, threshold_ms: float = 1000) -> list[NetworkEntry]:
        """Return requests that took longer than threshold_ms milliseconds."""
        return [e for e in self._log if e.duration_ms and e.duration_ms > threshold_ms]

    def summary(self) -> dict[str, Any]:
        total = len(self._log)
        failed = sum(1 for e in self._log if e.failed)
        by_type: dict[str, int] = {}
        for e in self._log:
            by_type[e.resource_type] = by_type.get(e.resource_type, 0) + 1
        durations = [e.duration_ms for e in self._log if e.duration_ms is not None]
        return {
            "total": total,
            "failed": failed,
            "by_resource_type": by_type,
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
        }

    def to_dicts(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._log]
