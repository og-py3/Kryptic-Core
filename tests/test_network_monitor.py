"""
Tests for NetworkMonitor.
"""
import asyncio
import pytest
from kryptic import Kryptic
from kryptic.network import NetworkMonitor, NetworkEntry


@pytest.mark.asyncio
async def test_monitor_captures_requests():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            return monitor.log

        log = await k.run(task)
        assert len(log) > 0
        assert all(isinstance(e, NetworkEntry) for e in log)


@pytest.mark.asyncio
async def test_monitor_captures_status():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            docs = monitor.filter(resource_type="document")
            return docs

        docs = await k.run(task)
        assert len(docs) >= 1
        assert all(e.status is not None for e in docs)
        assert any(e.status == 200 for e in docs)


@pytest.mark.asyncio
async def test_monitor_filter_by_type():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            return {
                "docs": len(monitor.filter(resource_type="document")),
                "all": len(monitor.log),
            }

        result = await k.run(task)
        assert result["docs"] >= 1
        assert result["all"] >= result["docs"]


@pytest.mark.asyncio
async def test_monitor_summary():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            return monitor.summary()

        summary = await k.run(task)
        assert "total" in summary
        assert "failed" in summary
        assert "by_resource_type" in summary
        assert summary["total"] > 0


@pytest.mark.asyncio
async def test_monitor_to_dicts():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            return monitor.to_dicts()

        dicts = await k.run(task)
        assert isinstance(dicts, list)
        assert len(dicts) > 0
        assert all(isinstance(d, dict) for d in dicts)
        assert all("url" in d for d in dicts)


@pytest.mark.asyncio
async def test_network_entry_duration():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            completed = [e for e in monitor.log if e.end_time is not None]
            return completed

        entries = await k.run(task)
        assert len(entries) > 0
        for e in entries:
            assert e.duration_ms is not None
            assert e.duration_ms >= 0


@pytest.mark.asyncio
async def test_monitor_filter_url_contains():
    async with Kryptic(headless=True, concurrency=1) as k:
        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()
            await page.goto("https://example.com", wait_until="networkidle")
            return monitor.filter(url_contains="example.com")

        entries = await k.run(task)
        assert len(entries) > 0
        assert all("example.com" in e.url for e in entries)
