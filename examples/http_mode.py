"""
HTTP-only mode: pure HTTP/S requests — no browser launched.
Perfect for APIs, sitemaps, status checks, or any page that doesn't need JS.

Run with:  PYTHONPATH=. python3 examples/http_mode.py
"""
import asyncio
from kryptic import Kryptic

URLS = [
    "https://httpbin.org/get",
    "https://httpbin.org/user-agent",
    "https://httpbin.org/headers",
    "https://httpbin.org/ip",
    "https://example.com",
]


async def main() -> None:
    async with Kryptic(mode="http", concurrency=20) as k:
        print(f"HTTP client ready: {k}\n")

        resp = await k.run(lambda http: http.get("https://httpbin.org/get"))
        print(f"Single GET → status {resp.status}")
        print(f"  URL:  {resp.url}")
        print(f"  JSON: {resp.json()}\n")

        timed = await k.batch_timed([
            (lambda u: lambda http: http.get(u))(url)
            for url in URLS
        ])

        for r in timed["results"]:
            print(f"  {r.status}  {r.url}")

        print(f"\n{len(URLS)} requests in {timed['total_seconds']}s "
              f"(avg {timed['avg_seconds']}s)")

        post_resp = await k.run(
            lambda http: http.post(
                "https://httpbin.org/post",
                json={"library": "kryptic", "fast": True},
            )
        )
        print(f"\nPOST → {post_resp.status}  data echoed: {post_resp.json().get('json')}")


asyncio.run(main())
