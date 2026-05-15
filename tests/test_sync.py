"""
Tests for KrypticSync (synchronous wrapper).
"""
import pytest
from kryptic.sync import KrypticSync


def test_sync_http_get():
    with KrypticSync(mode="http", concurrency=2) as k:
        resp = k.http_get("https://httpbin.org/status/200")
        assert resp.status == 200


def test_sync_http_post():
    with KrypticSync(mode="http", concurrency=1) as k:
        resp = k.http_post(
            "https://httpbin.org/post",
            json={"test": True},
        )
        assert resp.status in (200, 201), f"Unexpected status {resp.status}"
        if resp.status == 200:
            assert resp.json()["json"] == {"test": True}


def test_sync_batch():
    with KrypticSync(mode="http", concurrency=4) as k:
        tasks = [lambda http: http.get("https://example.com")] * 3
        results = k.batch(tasks)
        assert len(results) == 3
        assert all(r.status == 200 for r in results)


def test_sync_browser_title():
    with KrypticSync(headless=True, concurrency=1) as k:
        async def task(page):
            await page.block_resources(["image", "stylesheet", "font", "media"])
            await page.goto("https://example.com")
            return await page.title()

        title = k.run(task)
        assert "Example Domain" in title


def test_sync_repr():
    k = KrypticSync(mode="http")
    assert "KrypticSync" in repr(k)
