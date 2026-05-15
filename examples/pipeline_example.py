"""
Pipeline builder — compose multi-step browser flows with a chainable API.

Run with:  PYTHONPATH=. python3 examples/pipeline_example.py
"""
import asyncio
from kryptic import Kryptic
from kryptic.pipeline import Pipeline


async def main():
    async with Kryptic(headless=True, concurrency=1) as k:

        # Basic extraction pipeline
        result = await (
            Pipeline(k)
            .block(["image", "stylesheet", "font", "media"])
            .goto("https://example.com")
            .extract("title", "title", method="title")
            .extract("h1", "h1")
            .extract("url", "", method="url")
            .extract("link_count", "a[href]", method="count")
            .evaluate("protocol", "() => window.location.protocol")
            .run()
        )

        print("Pipeline result:")
        for k2, v in result.items():
            print(f"  {k2}: {v}")

        # Pipeline with wait + form-style interaction
        search_result = await (
            Pipeline(k)
            .block(["image", "font", "media"])
            .goto("https://httpbin.org/forms/post")
            .extract("form_title", "h2")
            .screenshot("pipeline_form.png")
            .run()
        )

        print("\nSearch pipeline:")
        for k3, v in search_result.items():
            print(f"  {k3}: {v}")


asyncio.run(main())
