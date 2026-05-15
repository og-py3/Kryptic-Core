"""
Tests for kryptic.extractors.
"""
import pytest
from kryptic import Kryptic
from kryptic import extractors


@pytest.mark.asyncio
async def test_extract_links():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await extractors.extract_links(page)

        links = await k.run(task)
        assert isinstance(links, list)
        assert len(links) > 0
        assert all("href" in l for l in links)


@pytest.mark.asyncio
async def test_extract_meta():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await extractors.extract_meta(page)

        meta = await k.run(task)
        assert isinstance(meta, dict)
        assert "title" in meta


@pytest.mark.asyncio
async def test_extract_text():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await extractors.extract_text(page)

        text = await k.run(task)
        assert isinstance(text, str)
        assert len(text) > 10


@pytest.mark.asyncio
async def test_extract_headings():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await extractors.extract_headings(page)

        headings = await k.run(task)
        assert isinstance(headings, dict)
        assert "h1" in headings
        assert isinstance(headings["h1"], list)
