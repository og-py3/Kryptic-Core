import asyncio
from typing import Any, Optional
import httpx


class HttpResponse:
    """Lightweight wrapper around an httpx response."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.status: int = response.status_code
        self.headers: dict[str, str] = dict(response.headers)
        self.url: str = str(response.url)
        self.body: str = response.text
        self.content: bytes = response.content

    def json(self) -> Any:
        return self._response.json()

    @property
    def ok(self) -> bool:
        return self.status < 400

    def __repr__(self) -> str:
        return f"HttpResponse(status={self.status}, url={self.url!r})"


class HttpClient:
    """
    Pure async HTTP client (no browser). Uses httpx with a shared connection
    pool and a semaphore to cap concurrency. Much faster than spinning up
    browsers when you only need raw HTTP responses.
    """

    def __init__(
        self,
        concurrency: int = 20,
        timeout: int = 30,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        follow_redirects: bool = True,
    ) -> None:
        self._semaphore = asyncio.Semaphore(concurrency)
        self._timeout = timeout
        self._user_agent = user_agent or (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        self._proxy = proxy
        self._follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None

    async def init(self) -> None:
        limits = httpx.Limits(
            max_connections=200,
            max_keepalive_connections=50,
        )
        headers = {"User-Agent": self._user_agent}
        proxies = self._proxy or None

        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=self._follow_redirects,
            limits=limits,
            headers=headers,
            proxy=proxies,
        )

    def _ensure_ready(self) -> None:
        if self._client is None:
            raise RuntimeError("HttpClient not initialised — call await client.init() first")

    async def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> HttpResponse:
        self._ensure_ready()
        async with self._semaphore:
            resp = await self._client.get(url, params=params, headers=headers or {})  # type: ignore[union-attr]
            return HttpResponse(resp)

    async def post(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> HttpResponse:
        self._ensure_ready()
        async with self._semaphore:
            resp = await self._client.post(url, data=data, json=json, headers=headers or {})  # type: ignore[union-attr]
            return HttpResponse(resp)

    async def put(
        self,
        url: str,
        json: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> HttpResponse:
        self._ensure_ready()
        async with self._semaphore:
            resp = await self._client.put(url, json=json, headers=headers or {})  # type: ignore[union-attr]
            return HttpResponse(resp)

    async def delete(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> HttpResponse:
        self._ensure_ready()
        async with self._semaphore:
            resp = await self._client.delete(url, headers=headers or {})  # type: ignore[union-attr]
            return HttpResponse(resp)

    async def head(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> HttpResponse:
        self._ensure_ready()
        async with self._semaphore:
            resp = await self._client.head(url, headers=headers or {})  # type: ignore[union-attr]
            return HttpResponse(resp)

    async def batch_get(self, urls: list[str]) -> list[HttpResponse]:
        """Fetch multiple URLs in parallel, respecting the concurrency cap."""
        return list(await asyncio.gather(*[self.get(url) for url in urls]))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
