"""
Tests for the Kryptic HTTP server using aiohttp TestClient (in-process).
Browser tests reuse one shared session for speed.
"""
import base64
import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient

from kryptic.server.app import create_app


@pytest_asyncio.fixture
async def client(aiohttp_client):
    """Per-test in-process server."""
    app = create_app(concurrency=2, headless=True)
    return await aiohttp_client(app)


# ── helpers ────────────────────────────────────────────────────────────────────

async def _new_session(client):
    r = await client.post("/sessions", json={})
    return (await r.json())["session_id"]


async def _goto_example(client, sid):
    await client.post(f"/sessions/{sid}/block", json={
        "resource_types": ["image", "stylesheet", "font", "media"]
    })
    await client.post(f"/sessions/{sid}/goto", json={"url": "https://example.com"})


# ── health ─────────────────────────────────────────────────────────────────────

async def test_health_ok(client):
    resp = await client.get("/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["ok"] is True
    assert "version" in data
    assert "sessions" in data


async def test_health_session_count_is_int(client):
    data = await (await client.get("/health")).json()
    assert isinstance(data["sessions"], int)


# ── sessions ───────────────────────────────────────────────────────────────────

async def test_create_and_close_session(client):
    r = await client.post("/sessions", json={})
    data = await r.json()
    assert data["ok"] is True
    sid = data["session_id"]
    assert len(sid) > 0
    close = await (await client.delete(f"/sessions/{sid}")).json()
    assert close["ok"] is True


async def test_close_nonexistent_session(client):
    resp = await client.delete("/sessions/no-such-session-xyz")
    assert resp.status == 404
    data = await resp.json()
    assert data["ok"] is False


# ── page actions (shared browser session) ─────────────────────────────────────

async def test_page_goto_and_title(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.get(f"/sessions/{sid}/title")).json()
    assert data["ok"] is True
    assert "Example Domain" in data["title"]
    await client.delete(f"/sessions/{sid}")


async def test_page_goto_and_html(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.get(f"/sessions/{sid}/html")).json()
    assert data["ok"] is True
    assert "<html" in data["html"].lower()
    await client.delete(f"/sessions/{sid}")


async def test_page_url(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.get(f"/sessions/{sid}/url")).json()
    assert "example.com" in data["url"]
    await client.delete(f"/sessions/{sid}")


async def test_page_text(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.post(f"/sessions/{sid}/text", json={"selector": "h1"})).json()
    assert data["ok"] is True
    assert "Example Domain" in data["text"]
    await client.delete(f"/sessions/{sid}")


async def test_page_evaluate(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.post(f"/sessions/{sid}/evaluate", json={"js": "() => 2 + 2"})).json()
    assert data["ok"] is True
    assert data["result"] == 4
    await client.delete(f"/sessions/{sid}")


async def test_page_find(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.post(f"/sessions/{sid}/find", json={"selector": "a"})).json()
    assert data["ok"] is True
    assert data["count"] >= 1
    await client.delete(f"/sessions/{sid}")


async def test_page_screenshot_is_png(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    data = await (await client.post(f"/sessions/{sid}/screenshot", json={})).json()
    assert data["ok"] is True
    assert data["encoding"] == "base64"
    assert base64.b64decode(data["data"])[:4] == b"\x89PNG"
    await client.delete(f"/sessions/{sid}")


async def test_block_resources_returns_blocked_list(client):
    sid = await _new_session(client)
    data = await (await client.post(f"/sessions/{sid}/block", json={
        "resource_types": ["image", "font"]
    })).json()
    assert data["ok"] is True
    assert data["blocked"] == ["image", "font"]
    await client.delete(f"/sessions/{sid}")


# ── validation errors ──────────────────────────────────────────────────────────

async def test_goto_missing_url_returns_400(client):
    sid = await _new_session(client)
    r = await client.post(f"/sessions/{sid}/goto", json={})
    assert r.status == 400
    await client.delete(f"/sessions/{sid}")


async def test_text_missing_selector_returns_400(client):
    sid = await _new_session(client)
    await _goto_example(client, sid)
    r = await client.post(f"/sessions/{sid}/text", json={})
    assert r.status == 400
    await client.delete(f"/sessions/{sid}")


async def test_evaluate_missing_js_returns_400(client):
    sid = await _new_session(client)
    r = await client.post(f"/sessions/{sid}/evaluate", json={})
    assert r.status == 400
    await client.delete(f"/sessions/{sid}")


# ── HTTP proxy endpoints ───────────────────────────────────────────────────────

async def test_http_get_endpoint(client):
    r = await client.post("/http/get", json={"url": "https://example.com"})
    data = await r.json()
    assert data["ok"] is True
    assert data["status"] == 200


async def test_http_post_endpoint(client):
    r = await client.post("/http/post", json={
        "url": "https://httpbin.org/post",
        "json": {"hello": "world"},
    })
    data = await r.json()
    assert data["ok"] is True
    assert data["status"] == 200


async def test_http_batch_endpoint(client):
    r = await client.post("/http/batch", json={
        "urls": ["https://example.com", "https://example.org"],
    })
    data = await r.json()
    assert data["ok"] is True
    assert len(data["results"]) == 2
    assert all(item["status"] == 200 for item in data["results"])


async def test_http_get_missing_url_returns_400(client):
    r = await client.post("/http/get", json={})
    assert r.status == 400
