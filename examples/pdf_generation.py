"""
PDF generation — save any web page as a PDF.

Note: PDF generation is Chromium-only.

Run with:  PYTHONPATH=. python3 examples/pdf_generation.py
"""
import asyncio
import os
from kryptic import Kryptic


async def main():
    async with Kryptic(headless=True, concurrency=1) as k:

        async def generate_pdf(page):
            await page.goto("https://example.com", wait_until="networkidle")

            # Full-page PDF, A4, with background colours
            pdf_bytes = await page.pdf(
                path="example.pdf",
                format="A4",
                print_background=True,
                margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
            )
            return len(pdf_bytes)

        size = await k.run(generate_pdf)
        print(f"PDF saved: example.pdf ({size} bytes)")
        assert os.path.exists("example.pdf")
        os.remove("example.pdf")
        print("Cleaned up example.pdf")

        # Multiple pages → multiple PDFs in parallel
        pages_to_pdf = [
            ("https://example.com", "out_example.pdf"),
            ("https://example.org", "out_example_org.pdf"),
        ]

        def make_pdf_task(url: str, out: str):
            async def task(page):
                await page.goto(url, wait_until="networkidle")
                await page.pdf(path=out)
                return out
            return task

        paths = await k.batch([make_pdf_task(u, o) for u, o in pages_to_pdf])
        for path in paths:
            print(f"Generated: {path} ({os.path.getsize(path)} bytes)")
            os.remove(path)


asyncio.run(main())
