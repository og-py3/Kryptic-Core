"""
Kryptic HTTP server — exposes browser automation and HTTP requests as a
local JSON REST API so any language can drive Kryptic over HTTP.

Start with:
    python -m kryptic serve [--port 7890] [--concurrency 4] [--headless]
"""
import asyncio
import base64
import json
import uuid
from typing import Any, Optional

from aiohttp import web

from ..core import Kryptic
from ..context import PageContext
from ..http_client import HttpClient
from ..pool import BrowserPool


# ── session store ────────────────────────────────────────────────────────────

class _Session:
    def __init__(self, context: Any, page_ctx: PageContext) -> None:
        self.context = context
        self.page_ctx = page_ctx


_sessions: dict[str, _Session] = {}
_pool: Optional[BrowserPool] = None
_http: Optional[HttpClient] = None


# ── helpers ───────────────────────────────────────────────────────────────────

def _ok(data: Any = None) -> web.Response:
    return web.Response(
        text=json.dumps({"ok": True, **(data or {})}),
        content_type="application/json",
    )


def _err(msg: str, status: int = 400) -> web.Response:
    return web.Response(
        text=json.dumps({"ok": False, "error": msg}),
        content_type="application/json",
        status=status,
    )


async def _body(req: web.Request) -> dict:
    try:
        return await req.json()
    except Exception:
        return {}


def _get_session(session_id: str) -> Optional[_Session]:
    return _sessions.get(session_id)


# ── routes ────────────────────────────────────────────────────────────────────

async def health(_req: web.Request) -> web.Response:
    from .. import __version__
    return _ok({"version": __version__, "sessions": len(_sessions)})


async def sessions_create(req: web.Request) -> web.Response:
    assert _pool is not None
    data = await _body(req)
    browser = await _pool.acquire()
    ctx = await browser.new_context()
    page = await ctx.new_page()
    page_ctx = PageContext(page)

    sid = str(uuid.uuid4())
    _sessions[sid] = _Session(context=ctx, page_ctx=page_ctx)

    req.app["_browsers"][sid] = browser
    return _ok({"session_id": sid})


async def sessions_close(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)

    await sess.context.close()
    del _sessions[sid]

    browser = req.app["_browsers"].pop(sid, None)
    if browser and _pool:
        await _pool.release(browser)

    return _ok()


async def page_goto(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    url = data.get("url")
    if not url:
        return _err("url required")
    wait = data.get("wait_until", "domcontentloaded")
    await sess.page_ctx.goto(url, wait_until=wait)
    return _ok({"url": sess.page_ctx.url})


async def page_title(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    title = await sess.page_ctx.title()
    return _ok({"title": title})


async def page_html(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    html = await sess.page_ctx.html()
    return _ok({"html": html})


async def page_url(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    return _ok({"url": sess.page_ctx.url})


async def page_text(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    selector = data.get("selector")
    if not selector:
        return _err("selector required")
    text = await sess.page_ctx.text(selector)
    return _ok({"text": text})


async def page_click(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    selector = data.get("selector")
    if not selector:
        return _err("selector required")
    await sess.page_ctx.click(selector)
    return _ok()


async def page_fill(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    selector = data.get("selector")
    value = data.get("value", "")
    if not selector:
        return _err("selector required")
    await sess.page_ctx.fill(selector, value)
    return _ok()


async def page_evaluate(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    js = data.get("js")
    if not js:
        return _err("js required")
    result = await sess.page_ctx.evaluate(js)
    return _ok({"result": result})


async def page_find(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    selector = data.get("selector")
    if not selector:
        return _err("selector required")
    elements = await sess.page_ctx.find(selector)
    texts = [await el.text() for el in elements]
    return _ok({"count": len(elements), "texts": texts})


async def page_screenshot(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    full_page = data.get("full_page", False)
    raw = await sess.page_ctx.screenshot_bytes(full_page=full_page)
    encoded = base64.b64encode(raw).decode()
    return _ok({"data": encoded, "encoding": "base64"})


async def page_block(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    types = data.get("resource_types", ["image", "stylesheet", "font", "media"])
    await sess.page_ctx.block_resources(types)
    return _ok({"blocked": types})


async def page_wait_for(req: web.Request) -> web.Response:
    sid = req.match_info["id"]
    sess = _get_session(sid)
    if not sess:
        return _err("session not found", 404)
    data = await _body(req)
    selector = data.get("selector")
    if not selector:
        return _err("selector required")
    state = data.get("state", "visible")
    await sess.page_ctx.wait_for(selector, state=state)
    return _ok()


async def http_get(req: web.Request) -> web.Response:
    assert _http is not None
    data = await _body(req)
    url = data.get("url")
    if not url:
        return _err("url required")
    resp = await _http.get(url, headers=data.get("headers"))
    return _ok({"status": resp.status, "body": resp.body, "headers": resp.headers})


async def http_post(req: web.Request) -> web.Response:
    assert _http is not None
    data = await _body(req)
    url = data.get("url")
    if not url:
        return _err("url required")
    resp = await _http.post(
        url,
        json=data.get("json"),
        data=data.get("data"),
        headers=data.get("headers"),
    )
    return _ok({"status": resp.status, "body": resp.body, "headers": resp.headers})


async def http_batch(req: web.Request) -> web.Response:
    assert _http is not None
    data = await _body(req)
    urls = data.get("urls", [])
    if not urls:
        return _err("urls required")
    responses = await _http.batch_get(urls)
    results = [{"status": r.status, "url": r.url, "body": r.body} for r in responses]
    return _ok({"results": results})


# ── app factory ───────────────────────────────────────────────────────────────

def create_app(
    concurrency: int = 4,
    headless: bool = True,
    http_concurrency: int = 20,
) -> web.Application:
    app = web.Application()
    app["_browsers"] = {}

    async def startup(application: web.Application) -> None:
        global _pool, _http
        from ..types import BrowserTypeName
        _pool = BrowserPool(
            concurrency=concurrency,
            headless=headless,
            browser_types=["chromium"],
        )
        await _pool.init()
        _http = HttpClient(concurrency=http_concurrency)
        await _http.init()

    async def cleanup(application: web.Application) -> None:
        for sid, sess in list(_sessions.items()):
            try:
                await sess.context.close()
            except Exception:
                pass
        _sessions.clear()
        if _pool:
            await _pool.close()
        if _http:
            await _http.close()

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    app.router.add_get("/health", health)

    app.router.add_post("/sessions", sessions_create)
    app.router.add_delete("/sessions/{id}", sessions_close)
    app.router.add_post("/sessions/{id}/goto", page_goto)
    app.router.add_get("/sessions/{id}/title", page_title)
    app.router.add_get("/sessions/{id}/html", page_html)
    app.router.add_get("/sessions/{id}/url", page_url)
    app.router.add_post("/sessions/{id}/text", page_text)
    app.router.add_post("/sessions/{id}/click", page_click)
    app.router.add_post("/sessions/{id}/fill", page_fill)
    app.router.add_post("/sessions/{id}/evaluate", page_evaluate)
    app.router.add_post("/sessions/{id}/find", page_find)
    app.router.add_post("/sessions/{id}/screenshot", page_screenshot)
    app.router.add_post("/sessions/{id}/block", page_block)
    app.router.add_post("/sessions/{id}/wait_for", page_wait_for)

    app.router.add_post("/http/get", http_get)
    app.router.add_post("/http/post", http_post)
    app.router.add_post("/http/batch", http_batch)

    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 7890,
    concurrency: int = 4,
    headless: bool = True,
) -> None:
    app = create_app(concurrency=concurrency, headless=headless)
    print(f"Kryptic server listening on http://{host}:{port}")
    web.run_app(app, host=host, port=port, print=None)
