"""
Kryptic CLI

Commands:
    kryptic serve      — Start the JSON HTTP server
    kryptic detect     — Detect installed browsers
    kryptic scrape     — Quick scrape a URL to stdout
    kryptic screenshot — Take a screenshot of a URL
    kryptic fetch      — HTTP GET a URL (no browser)
    kryptic ping       — Check if a URL is reachable
    kryptic snapshot   — Full structured data snapshot of a page
"""
import argparse
import asyncio
import json
import sys


# ── serve ─────────────────────────────────────────────────────────────────────

def cmd_serve(args: argparse.Namespace) -> None:
    from .server import run_server
    run_server(
        host=args.host,
        port=args.port,
        concurrency=args.concurrency,
        headless=not args.no_headless,
    )


# ── detect ────────────────────────────────────────────────────────────────────

def cmd_detect(_args: argparse.Namespace) -> None:
    from .utils import detect_browsers

    async def _run() -> None:
        results = await detect_browsers()
        print("Installed browsers:")
        for b in results:
            mark = "✓" if b["available"] else "✗"
            print(f"  {mark}  {b['name']}")
        available = [b["name"] for b in results if b["available"]]
        if not available:
            print("\nNo browsers found. Run: python -m playwright install chromium")
            sys.exit(1)

    asyncio.run(_run())


# ── scrape ────────────────────────────────────────────────────────────────────

def cmd_scrape(args: argparse.Namespace) -> None:
    from .core import Kryptic

    async def _run() -> None:
        async with Kryptic(headless=True, concurrency=1) as k:
            async def task(page):
                await page.block_resources(["image", "stylesheet", "font", "media"])
                await page.goto(args.url)
                title = await page.title()
                h1_els = await page.find("h1")
                h1 = await h1_els[0].text() if h1_els else ""
                links_raw = await page.find("a[href]")
                links = []
                for el in links_raw[:args.max_links]:
                    href = await el.attr("href")
                    text = await el.text()
                    if href:
                        links.append({"text": text.strip(), "href": href})
                return {
                    "url": page.url,
                    "title": title,
                    "h1": h1,
                    "links": links,
                }

            result = await k.run(task)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"URL:   {result['url']}")
                print(f"Title: {result['title']}")
                print(f"H1:    {result['h1']}")
                print(f"\nLinks ({len(result['links'])}):")
                for l in result["links"]:
                    print(f"  {l['href']}")

    asyncio.run(_run())


# ── screenshot ────────────────────────────────────────────────────────────────

def cmd_screenshot(args: argparse.Namespace) -> None:
    from .core import Kryptic

    async def _run() -> None:
        async with Kryptic(headless=True, concurrency=1) as k:
            async def task(page):
                await page.goto(args.url, wait_until="networkidle")
                await page.screenshot(args.output, full_page=args.full_page)
                return args.output

            path = await k.run(task)
            print(f"Screenshot saved: {path}")

    asyncio.run(_run())


# ── fetch ─────────────────────────────────────────────────────────────────────

def cmd_fetch(args: argparse.Namespace) -> None:
    from .core import Kryptic

    async def _run() -> None:
        async with Kryptic(mode="http", concurrency=1) as k:
            resp = await k.run(lambda http: http.get(args.url))
            if args.json:
                print(json.dumps({
                    "status": resp.status,
                    "url": resp.url,
                    "headers": resp.headers,
                    "body": resp.body[:args.max_body] if args.max_body else resp.body,
                }, indent=2))
            else:
                print(f"Status: {resp.status}")
                print(f"URL:    {resp.url}")
                if args.headers:
                    for k2, v in resp.headers.items():
                        print(f"  {k2}: {v}")
                print()
                print(resp.body[:args.max_body] if args.max_body else resp.body)

    asyncio.run(_run())


# ── ping ──────────────────────────────────────────────────────────────────────

def cmd_ping(args: argparse.Namespace) -> None:
    from .core import Kryptic
    import time

    async def _run() -> None:
        async with Kryptic(mode="http", concurrency=1) as k:
            for url in args.urls:
                t0 = time.perf_counter()
                try:
                    resp = await k.run(lambda http: http.get(url))
                    ms = round((time.perf_counter() - t0) * 1000, 1)
                    ok = "✓" if resp.ok else "✗"
                    print(f"  {ok}  {resp.status}  {ms}ms  {url}")
                except Exception as e:
                    ms = round((time.perf_counter() - t0) * 1000, 1)
                    print(f"  ✗  ERR  {ms}ms  {url}  ({e})")

    asyncio.run(_run())


# ── snapshot ──────────────────────────────────────────────────────────────────

def cmd_snapshot(args: argparse.Namespace) -> None:
    from .core import Kryptic
    from .extractors import snapshot

    async def _run() -> None:
        async with Kryptic(headless=True, concurrency=1) as k:
            async def task(page):
                await page.block_resources(["image", "stylesheet", "font", "media"])
                await page.goto(args.url)
                return await snapshot(page)

            data = await k.run(task)
            print(json.dumps(data, indent=2))

    asyncio.run(_run())


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kryptic",
        description="Kryptic — fast headless browser automation",
    )
    sub = parser.add_subparsers(dest="command")

    # serve
    sp = sub.add_parser("serve", help="Start the Kryptic JSON HTTP server")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=7890)
    sp.add_argument("--concurrency", type=int, default=4)
    sp.add_argument("--no-headless", action="store_true")

    # detect
    sub.add_parser("detect", help="Detect installed Playwright browsers")

    # scrape
    sc = sub.add_parser("scrape", help="Quick-scrape a URL")
    sc.add_argument("url")
    sc.add_argument("--max-links", type=int, default=20)
    sc.add_argument("--json", action="store_true")

    # screenshot
    ss = sub.add_parser("screenshot", help="Take a screenshot")
    ss.add_argument("url")
    ss.add_argument("output", nargs="?", default="screenshot.png")
    ss.add_argument("--full-page", action="store_true")

    # fetch
    fe = sub.add_parser("fetch", help="HTTP GET (no browser)")
    fe.add_argument("url")
    fe.add_argument("--json", action="store_true")
    fe.add_argument("--headers", action="store_true")
    fe.add_argument("--max-body", type=int, default=0)

    # ping
    pi = sub.add_parser("ping", help="Check URL(s) reachability")
    pi.add_argument("urls", nargs="+")

    # snapshot
    sn = sub.add_parser("snapshot", help="Full structured data snapshot (JSON)")
    sn.add_argument("url")

    args = parser.parse_args()
    dispatch = {
        "serve": cmd_serve,
        "detect": cmd_detect,
        "scrape": cmd_scrape,
        "screenshot": cmd_screenshot,
        "fetch": cmd_fetch,
        "ping": cmd_ping,
        "snapshot": cmd_snapshot,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
