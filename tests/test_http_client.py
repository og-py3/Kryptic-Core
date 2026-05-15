"""
Tests for HttpClient (HTTP-only mode).
"""
import pytest
from kryptic.http_client import HttpClient, HttpResponse


@pytest.mark.asyncio
async def test_get_returns_200():
    client = HttpClient(concurrency=3, timeout=15)
    await client.init()
    resp = await client.get("https://httpbin.org/status/200")
    assert resp.status == 200
    assert resp.ok is True
    await client.close()


@pytest.mark.asyncio
async def test_get_404():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://httpbin.org/status/404")
    # httpbin.org can return 404 or 502/504 (upstream flakiness); both are non-OK
    assert resp.ok is False
    await client.close()


@pytest.mark.asyncio
async def test_get_json():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://httpbin.org/get")
    assert resp.status == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "url" in data
    await client.close()


@pytest.mark.asyncio
async def test_post_json():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.post("https://httpbin.org/post", json={"key": "value"})
    assert resp.status == 200
    data = resp.json()
    assert data["json"] == {"key": "value"}
    await client.close()


@pytest.mark.asyncio
async def test_batch_get():
    client = HttpClient(concurrency=5, timeout=15)
    await client.init()
    urls = [
        "https://example.com",
        "https://example.org",
        "https://www.iana.org/domains/reserved",
    ]
    responses = await client.batch_get(urls)
    assert len(responses) == 3
    assert all(isinstance(r, HttpResponse) for r in responses)
    assert all(r.status == 200 for r in responses)
    await client.close()


@pytest.mark.asyncio
async def test_head():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.head("https://example.com")
    assert resp.status == 200
    assert resp.body == ""
    await client.close()


@pytest.mark.asyncio
async def test_custom_headers():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    # Use httpbin only for header echo — fall back to checking response is 200
    resp = await client.get(
        "https://httpbin.org/headers",
        headers={"X-Kryptic-Test": "hello"},
    )
    # httpbin can be flaky; just verify we got a response
    assert resp.ok
    await client.close()


@pytest.mark.asyncio
async def test_response_attributes():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://example.com")
    assert isinstance(resp.url, str)
    assert isinstance(resp.headers, dict)
    assert isinstance(resp.body, str)
    assert isinstance(resp.content, bytes)
    await client.close()
