"""
Tests for HttpResponse and HttpClient edge cases.
"""
import pytest
from kryptic.http_client import HttpClient, HttpResponse


@pytest.mark.asyncio
async def test_not_initialised_raises():
    client = HttpClient()
    with pytest.raises(RuntimeError, match="not initialised"):
        await client.get("https://example.com")


@pytest.mark.asyncio
async def test_ok_property_true():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://httpbin.org/status/200")
    assert resp.ok is True
    await client.close()


@pytest.mark.asyncio
async def test_ok_property_false_on_error():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://httpbin.org/status/500")
    assert resp.ok is False
    await client.close()


@pytest.mark.asyncio
async def test_put_request():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.put("https://httpbin.org/put", json={"key": "val"})
    assert resp.status == 200
    await client.close()


@pytest.mark.asyncio
async def test_delete_request():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.delete("https://httpbin.org/delete")
    assert resp.status == 200
    await client.close()


@pytest.mark.asyncio
async def test_response_repr():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://httpbin.org/status/200")
    r = repr(resp)
    assert "HttpResponse" in r
    assert "200" in r
    await client.close()


@pytest.mark.asyncio
async def test_follow_redirects():
    client = HttpClient(concurrency=1, timeout=15, follow_redirects=True)
    await client.init()
    resp = await client.get("https://httpbin.org/redirect/2")
    assert resp.status == 200
    await client.close()


@pytest.mark.asyncio
async def test_batch_returns_correct_order():
    client = HttpClient(concurrency=10, timeout=15)
    await client.init()
    urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/201",
        "https://httpbin.org/status/202",
        "https://httpbin.org/status/203",
        "https://httpbin.org/status/204",
    ]
    responses = await client.batch_get(urls)
    statuses = [r.status for r in responses]
    assert statuses == [200, 201, 202, 203, 204]
    await client.close()


@pytest.mark.asyncio
async def test_get_with_query_params():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get(
        "https://httpbin.org/get",
        params={"foo": "bar", "num": "42"},
    )
    assert resp.status == 200
    data = resp.json()
    assert data["args"]["foo"] == "bar"
    assert data["args"]["num"] == "42"
    await client.close()


@pytest.mark.asyncio
async def test_response_content_bytes():
    client = HttpClient(concurrency=1, timeout=15)
    await client.init()
    resp = await client.get("https://example.com")
    assert isinstance(resp.content, bytes)
    assert len(resp.content) > 0
    await client.close()
