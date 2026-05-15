"""
Edge case tests for the core Kryptic class.
"""
import asyncio
import pytest
from kryptic import Kryptic


@pytest.mark.asyncio
async def test_not_ready_raises():
    k = Kryptic(mode="http")
    with pytest.raises(RuntimeError, match="not initialised"):
        await k.run(lambda http: http.get("https://example.com"))


@pytest.mark.asyncio
async def test_double_close_safe():
    k = Kryptic(mode="http", concurrency=1)
    await k.init()
    await k.close()
    await k.close()  # second close should not raise


@pytest.mark.asyncio
async def test_mode_property():
    async with Kryptic(mode="http") as k:
        assert k.mode == "http"


@pytest.mark.asyncio
async def test_browser_mode_property():
    async with Kryptic(mode="browser", concurrency=1) as k:
        assert k.mode == "browser"


@pytest.mark.asyncio
async def test_concurrency_property():
    async with Kryptic(mode="http", concurrency=7) as k:
        assert k.concurrency == 7


@pytest.mark.asyncio
async def test_pool_size_http_mode():
    async with Kryptic(mode="http", concurrency=3) as k:
        assert k.pool_size == 0  # no browser pool in http mode


@pytest.mark.asyncio
async def test_pool_size_browser_mode():
    async with Kryptic(mode="browser", concurrency=2) as k:
        assert k.pool_size == 2


@pytest.mark.asyncio
async def test_empty_batch_returns_empty():
    async with Kryptic(mode="http", concurrency=1) as k:
        results = await k.batch([])
        assert results == []


@pytest.mark.asyncio
async def test_batch_timed_empty():
    async with Kryptic(mode="http", concurrency=1) as k:
        timed = await k.batch_timed([])
        assert timed["tasks"] == 0
        assert timed["results"] == []


@pytest.mark.asyncio
async def test_batch_preserves_order():
    async with Kryptic(mode="http", concurrency=10) as k:
        expected = list(range(10))
        tasks = [(lambda i: lambda _: asyncio.coroutine(lambda: i)())(n) for n in expected]

        async def make_task(n):
            async def t(_):
                return n
            return t

        real_tasks = [await make_task(n) for n in expected]
        results = await k.batch(real_tasks)
        assert results == expected


@pytest.mark.asyncio
async def test_concurrent_http_tasks():
    async with Kryptic(mode="http", concurrency=10) as k:
        tasks = [lambda http: http.get("https://httpbin.org/status/200")] * 10
        results = await k.batch(tasks)
        assert all(r.status == 200 for r in results)


@pytest.mark.asyncio
async def test_custom_user_agent():
    async with Kryptic(mode="http", concurrency=1, user_agent="TestAgent/1.0") as k:
        resp = await k.run(lambda http: http.get("https://httpbin.org/user-agent"))
        assert resp.status == 200
        data = resp.json()
        assert data["user-agent"] == "TestAgent/1.0"


@pytest.mark.asyncio
async def test_timeout_propagated():
    k = Kryptic(mode="http", timeout=5000)
    assert k._timeout == 5000
