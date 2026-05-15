"""
Request interception: block unwanted resource types, log requests,
or mock API responses — all at full speed.

Run with:  PYTHONPATH=. python3 examples/intercept_requests.py
"""
import asyncio
from kryptic import Kryptic


async def main() -> None:
    async with Kryptic(headless=True, concurrency=1) as k:

        print("=== Intercepted requests on example.com ===")
        intercepted: list[str] = []

        async def log_and_filter(page):
            async def handler(route, request):
                if request.resource_type in ("image", "font", "media"):
                    await route.abort()
                else:
                    intercepted.append(f"{request.method} {request.url[:80]}")
                    await route.continue_()

            await page.intercept("**/*", handler)
            await page.goto("https://example.com")
            return await page.title()

        title = await k.run(log_and_filter)
        print(f"Title: {title}")
        print(f"Requests allowed through ({len(intercepted)}):")
        for req in intercepted[:10]:
            print(f"  {req}")

        print("\n=== Mocked API response ===")

        async def mock_api(page):
            async def mock_handler(route, request):
                if "httpbin.org/get" in request.url:
                    await route.fulfill(
                        status=200,
                        content_type="application/json",
                        body='{"mocked": true, "library": "kryptic"}',
                    )
                else:
                    await route.continue_()

            await page.intercept("**/*", mock_handler)
            await page.goto("https://httpbin.org/get")
            body = await page.html()
            return body[:300]

        html = await k.run(mock_api)
        print(f"Body preview: {html}")


asyncio.run(main())
