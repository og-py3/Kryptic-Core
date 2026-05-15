"""
Tests for the core Kryptic class.
"""
import asyncio
import pytest
from kryptic import Kryptic
from kryptic.context import PageContext


@pytest.mark.asyncio
async def test_http_mode_basic():
    async with Kryptic(mode="http", concurrency=2) as k:
        resp = await k.run(lambda http: http.get("https://httpbin.org/status/200"))
        assert resp.status == 200


@pytest.mark.asyncio
async def test_http_mode_batch():
    async with Kryptic(mode="http", concurrency=4) as k:
        tasks = [lambda http: http.get("https://httpbin.org/status/200")] * 4
        results = await k.batch(tasks)
        assert all(r.status == 200 for r in results)


@pytest.mark.asyncio
async def test_http_batch_timed():
    async with Kryptic(mode="http", concurrency=2) as k:
        tasks = [lambda http: http.get("https://example.com")] * 2
        timed = await k.batch_timed(tasks)
        assert "results" in timed
        assert "total_seconds" in timed
        assert "avg_seconds" in timed
        assert timed["tasks"] == 2
        assert len(timed["results"]) == 2


@pytest.mark.asyncio
async def test_browser_mode_title():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page: PageContext):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await page.title()

        title = await k.run(task)
        assert "Example Domain" in title


@pytest.mark.asyncio
async def test_browser_mode_text():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page: PageContext):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await page.text("h1")

        text = await k.run(task)
        assert "Example Domain" in text


@pytest.mark.asyncio
async def test_browser_mode_evaluate():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page: PageContext):
            await page.goto("https://example.com")
            return await page.evaluate("() => document.title")

        title = await k.run(task)
        assert isinstance(title, str)
        assert len(title) > 0


@pytest.mark.asyncio
async def test_browser_mode_find():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page: PageContext):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            links = await page.find("a")
            return len(links)

        count = await k.run(task)
        assert count > 0


@pytest.mark.asyncio
async def test_context_manager():
    k = Kryptic(mode="http", concurrency=1)
    async with k:
        resp = await k.run(lambda http: http.get("https://example.com"))
        assert resp.status == 200


@pytest.mark.asyncio
async def test_repr():
    k = Kryptic(mode="http", concurrency=5)
    r = repr(k)
    assert "Kryptic" in r
    assert "http" in r
