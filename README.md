# Kryptic

> **Fast, concurrent browser automation for Python — and any language.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/kryptic)](https://pypi.org/project/kryptic/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Languages](https://img.shields.io/badge/Bindings-JS%20%7C%20Java%20%7C%20Go%20%7C%20Rust%20%7C%20C%20%7C%20C%2B%2B%20%7C%20PHP%20%7C%20Ruby-green)](#use-from-any-language)
[![polyrun](https://img.shields.io/badge/polyrun-compatible-blueviolet)](https://pypi.org/project/polyrun/)

---

Kryptic is a headless browser automation library built for speed. It pools multiple browser instances, runs tasks in parallel across them, and includes an HTTP-only mode that skips the browser entirely. A built-in JSON server lets you drive Kryptic from **any programming language** — directly via the bindings, or via [polyrun](https://pypi.org/project/polyrun/).

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modes](#modes)
- [API Reference](#api-reference)
- [Use from Any Language](#use-from-any-language)
- [polyrun Integration](#polyrun-integration)
- [Server API](#server-api)
- [Stealth Mode](#stealth-mode)
- [Retry Logic](#retry-logic)
- [Pipeline Builder](#pipeline-builder)
- [Data Extraction](#data-extraction)
- [Network Monitoring](#network-monitoring)
- [Mobile Emulation](#mobile-emulation)
- [Storage Persistence](#storage-persistence)
- [Proxy Rotation](#proxy-rotation)
- [Synchronous API](#synchronous-api)
- [CLI](#cli)
- [Examples](#examples)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Browser pool** — N browser instances run in parallel; tasks queue automatically
- **HTTP-only mode** — skip the browser entirely; pure async HTTP with connection pooling
- **Stealth mode** — randomise UA, viewport, locale, timezone, inject anti-bot JS
- **Retry + backoff** — `@retry` decorator and `with_retry()` for flaky pages
- **Chainable pipeline** — `.goto().click().fill().extract().screenshot().run()`
- **Data extractors** — links, images, meta, tables, emails, phones, JSON-LD, full snapshot
- **Network monitor** — capture, filter, and analyse all page requests
- **Mobile emulation** — 9 device profiles (iPhone, Galaxy, Pixel, iPad, Desktop)
- **Storage persistence** — save/restore cookies and localStorage across sessions
- **Proxy rotation** — round-robin or random, with per-proxy failure tracking
- **Infinite scroll** — auto-scroll until content stops growing
- **PDF generation** — export any page to PDF (Chromium)
- **Any language** — start Kryptic as a local HTTP server and call it from JS, Java, Go, Rust, C, C++, PHP, or Ruby — or use [polyrun](https://pypi.org/project/polyrun/) to run any binding directly from Python
- **Synchronous API** — `KrypticSync` lets you use Kryptic without writing async code
- **Full test suite** — 100+ pytest tests

---

## Installation

```bash
pip install kryptic
python -m playwright install chromium
```

With polyrun support (to run the language bindings from Python):

```bash
pip install "kryptic[polyglot]"
```

---

## Quick Start

```python
import asyncio
from kryptic import Kryptic

async def main():
    async with Kryptic(headless=True, concurrency=4) as k:

        async def scrape(page):
            await page.block_resources(["image", "stylesheet", "font"])
            await page.goto("https://example.com")
            return await page.title()

        print(await k.run(scrape))

        # Batch — all tasks fire in parallel across the pool
        results = await k.batch([scrape, scrape, scrape])
        print(results)

asyncio.run(main())
```

No asyncio? Use the synchronous wrapper:

```python
from kryptic.sync import KrypticSync

with KrypticSync(concurrency=4) as k:
    title = k.run(lambda page: (
        page.block_resources(["image", "stylesheet"]) or
        page.goto("https://example.com") or
        page.title()
    ))
```

HTTP-only mode (no browser):

```python
async with Kryptic(mode="http", concurrency=20) as k:
    resp = await k.run(lambda http: http.get("https://example.com"))
    print(resp.status, resp.body[:200])

    results = await k.batch([
        lambda http: http.get("https://example.com"),
        lambda http: http.get("https://example.org"),
    ])
```

---

## Modes

| Mode | When to use | Speed |
|------|-------------|-------|
| `browser` (default) | JavaScript-heavy pages, SPAs, login flows | ~0.5–2s/page |
| `http` | APIs, static pages, status checks, sitemaps | ~50–200ms/req |

---

## API Reference

### `Kryptic(mode, headless, concurrency, browser_types, timeout, user_agent, proxy)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `"browser"` \| `"http"` | `"browser"` | Execution mode |
| `headless` | `bool` | `True` | Headless browser |
| `concurrency` | `int` | `4` | Pool size |
| `browser_types` | `list` | `["chromium"]` | Browser types (`chromium`, `firefox`, `webkit`) |
| `timeout` | `int` | `30000` | Default timeout (ms) |
| `user_agent` | `str` | `None` | Override User-Agent |
| `proxy` | `str` | `None` | Proxy URL (`http://host:port`) |

### `PageContext` methods (browser mode)

| Method | Description |
|--------|-------------|
| `goto(url, wait_until)` | Navigate |
| `title()` / `html()` / `url` | Page info |
| `click(selector)` / `double_click()` / `right_click()` | Click |
| `fill(selector, value)` / `type_slowly()` / `clear()` | Input |
| `check(selector)` / `uncheck()` / `is_checked()` | Checkbox |
| `select(selector, value)` | Dropdown |
| `press(selector, key)` / `key(key)` | Keyboard |
| `hover(selector)` / `focus(selector)` / `tap(selector)` | Pointer |
| `drag_and_drop(source, target)` | Drag |
| `upload_file(selector, *paths)` | File input |
| `text(selector)` / `attr()` / `input_value()` | Read |
| `find(selector)` → `[Element]` / `find_one()` / `count()` / `exists()` | Query |
| `wait_for(selector, state)` / `wait_for_load()` / `wait_for_url()` | Wait |
| `evaluate(js)` / `evaluate_on(selector, js)` | JavaScript |
| `screenshot(path)` / `screenshot_bytes()` / `screenshot_element(selector)` | Screenshot |
| `pdf(path, format)` | PDF (Chromium only) |
| `block_resources(types)` / `block_ads()` | Speed |
| `intercept(pattern, handler)` | Network intercept |
| `set_headers(headers)` | Headers |
| `cookies()` / `set_cookies()` / `clear_cookies()` | Cookies |
| `on_dialog(handler)` / `auto_accept_dialogs()` | Dialogs |
| `frame(selector)` | iFrame access |
| `scroll_to_bottom()` / `scroll_by()` / `infinite_scroll()` | Scroll |
| `set_viewport(w, h)` / `emulate_device(name)` | Viewport |
| `metrics()` / `accessibility_tree()` | Performance |
| `reload()` / `go_back()` / `go_forward()` | Navigation |
| `add_script_tag()` / `add_style_tag()` | Inject |

### `HttpClient` methods (http mode)

`get()`, `post()`, `put()`, `delete()`, `head()`, `batch_get()`

### `HttpResponse` attributes

`.status`, `.ok`, `.url`, `.body`, `.content`, `.headers`, `.json()`

---

## Use from Any Language

Start the Kryptic server:

```bash
python -m kryptic serve --port 7890 --concurrency 4
```

Client bindings in `bindings/` — zero external dependencies:

| Language | File | Deps |
|---|---|---|
| **JavaScript** | `bindings/javascript/kryptic.js` | None (Node built-in `http`) |
| **Java** | `bindings/java/Kryptic.java` | None (Java 11+ built-in) |
| **Go** | `bindings/go/kryptic.go` | None (stdlib `net/http`) |
| **Rust** | `bindings/rust/kryptic.rs` | `ureq`, `serde_json` |
| **C** | `bindings/c/kryptic.h` / `.c` | libcurl |
| **C++** | `bindings/cpp/kryptic.hpp` | libcurl + nlohmann/json |
| **PHP** | `bindings/php/kryptic.php` | ext-curl (built-in) |
| **Ruby** | `bindings/ruby/kryptic.rb` | None (stdlib `Net::HTTP`) |

---

## polyrun Integration

[polyrun](https://pypi.org/project/polyrun/) is a lightweight polyglot execution framework — it lets you run any of the Kryptic language bindings **directly from Python**, with no manual compilation or runtime setup.

```bash
pip install "kryptic[polyglot]"
# or: pip install polyrun
```

```python
from polyrun import JS, Go, Java, Rust, C, Cpp

# Run the JavaScript binding
result = JS.run("""
    const http = require('http');
    // ... drive Kryptic server via JS
""", timeout=30)
print(result.stdout)

# Run the Go binding
result = Go.run("""
    package main
    import "fmt"
    func main() { fmt.Println("Hello from Go!") }
""")

# Run the Rust binding
result = Rust.run("""
    fn main() { println!("Hello from Rust!"); }
""", timeout=60)

# Run the Java binding
result = Java.run("""
    public class Main {
        public static void main(String[] args) {
            System.out.println("Hello from Java!");
        }
    }
""")
```

See `examples/polyrun_example.py` for a full working demo that drives the Kryptic server from JavaScript, Go, and Rust simultaneously.

---

## Server API

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | — | Server status and version |
| `POST` | `/sessions` | `{}` | Create a browser session |
| `DELETE` | `/sessions/{id}` | — | Close a session |
| `POST` | `/sessions/{id}/goto` | `{url, wait_until?}` | Navigate |
| `GET` | `/sessions/{id}/title` | — | Page title |
| `GET` | `/sessions/{id}/html` | — | Full HTML |
| `GET` | `/sessions/{id}/url` | — | Current URL |
| `POST` | `/sessions/{id}/text` | `{selector}` | Inner text |
| `POST` | `/sessions/{id}/click` | `{selector}` | Click |
| `POST` | `/sessions/{id}/fill` | `{selector, value}` | Fill input |
| `POST` | `/sessions/{id}/evaluate` | `{js}` | Execute JavaScript |
| `POST` | `/sessions/{id}/find` | `{selector}` | Find elements |
| `POST` | `/sessions/{id}/screenshot` | `{full_page?}` | Screenshot (base64 PNG) |
| `POST` | `/sessions/{id}/block` | `{resource_types}` | Block resource types |
| `POST` | `/sessions/{id}/wait_for` | `{selector, state?}` | Wait for element |
| `POST` | `/http/get` | `{url, headers?}` | HTTP GET |
| `POST` | `/http/post` | `{url, json?, data?}` | HTTP POST |
| `POST` | `/http/batch` | `{urls: [...]}` | Batch HTTP GETs |

All responses: `{"ok": true, ...}` or `{"ok": false, "error": "..."}`.

---

## Stealth Mode

```python
from kryptic.stealth import StealthProfile, random_profile

profile = random_profile(level="high")  # low / medium / high

async def task(page):
    await profile.apply(page)  # inject anti-bot JS, set random UA + viewport
    await page.goto("https://example.com")
```

---

## Retry Logic

```python
from kryptic.retry import retry, with_retry, RetryConfig

@retry(max_attempts=3, delay=1.0, backoff=2.0)
async def scrape(page):
    await page.goto("https://flaky-site.com")
    return await page.title()

# Inline:
result = await with_retry(my_task_fn, max_attempts=5, delay=0.5)

# Reusable config:
cfg = RetryConfig(max_attempts=4, delay=0.5, backoff=2.0)
result = await cfg.run(my_task_fn)
```

---

## Pipeline Builder

```python
from kryptic.pipeline import Pipeline

result = await (
    Pipeline(k)
    .block(["image", "stylesheet", "font"])
    .goto("https://example.com")
    .wait_for("h1")
    .extract("title", "title", method="title")
    .extract("heading", "h1")
    .extract("link_count", "a[href]", method="count")
    .screenshot("out.png")
    .run()
)
# {"title": "...", "heading": "...", "link_count": 3}
```

---

## Data Extraction

```python
from kryptic import extractors

async def task(page):
    await page.goto("https://example.com")
    links  = await extractors.extract_links(page)
    meta   = await extractors.extract_meta(page)
    emails = await extractors.extract_emails(page)
    tables = await extractors.extract_all_tables(page)
    snap   = await extractors.snapshot(page)   # full structured snapshot
```

---

## Network Monitoring

```python
from kryptic.network import NetworkMonitor

async def task(page):
    monitor = NetworkMonitor(page)
    await monitor.start()
    await page.goto("https://example.com", wait_until="networkidle")

    slow  = monitor.slow_requests(threshold_ms=500)
    api   = monitor.filter(resource_type="fetch")
    print(monitor.summary())
```

---

## Mobile Emulation

```python
from kryptic import list_devices

print(list_devices())
# ['Desktop 1080p', 'Desktop 4K', 'iPad Air', 'iPad Pro 12.9',
#  'iPhone 14', 'iPhone 14 Pro Max', 'iPhone SE', 'Pixel 7', 'Samsung Galaxy S23']

async def task(page):
    await page.emulate_device("iPhone 14")
    await page.goto("https://example.com")
```

---

## Storage Persistence

```python
from kryptic.storage import save_cookies, load_cookies

# After login — save
async def login(page):
    await page.goto("https://site.com/login")
    await page.fill("#email", "user@example.com")
    await page.fill("#pass", "secret")
    await page.click("[type=submit]")
    await save_cookies(page, "session.json")

# New session — restore
async def use_session(page):
    await load_cookies(page, "session.json")
    await page.goto("https://site.com/dashboard")
    return await page.title()
```

---

## Proxy Rotation

```python
from kryptic.proxy_pool import ProxyPool

pool = ProxyPool([
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
], strategy="round_robin")

async with Kryptic(proxy=pool.next()) as k:
    result = await k.run(my_task)
    pool.mark_failed(pool.next())  # if a proxy goes down
```

---

## Synchronous API

```python
from kryptic.sync import KrypticSync

with KrypticSync(mode="http", concurrency=10) as k:
    resp = k.http_get("https://example.com")
    results = k.batch([lambda http: http.get(url) for url in urls])
```

---

## CLI

```bash
kryptic serve --port 7890 --concurrency 4   # start JSON server
kryptic detect                               # check installed browsers
kryptic scrape https://example.com          # quick scrape to stdout
kryptic screenshot https://example.com out.png --full-page
kryptic fetch https://httpbin.org/get --json
kryptic ping https://example.com https://example.org
kryptic snapshot https://example.com        # full JSON snapshot
```

---

## Examples

```
examples/
  basic_usage.py           open a page, grab title and text
  parallel_scrape.py       6 pages × 3 browser instances
  http_mode.py             pure HTTP, no browser
  detect_browsers.py       auto-detect installed browsers
  intercept_requests.py    block resources, mock APIs
  server_mode.py           drive the JSON server from Python
  sync_usage.py            KrypticSync — no asyncio
  stealth_mode.py          randomised browser fingerprints
  pipeline_example.py      chainable Pipeline builder
  extractors_example.py    structured data extraction
  network_monitor.py       capture all network requests
  mobile_emulation.py      iPhone, Galaxy, iPad profiles
  infinite_scroll.py       scroll until content loads
  retry_example.py         automatic retry with backoff
  pdf_generation.py        export pages to PDF
  proxy_rotation.py        ProxyPool round-robin / random
  storage_persistence.py   save/restore cookies and localStorage
  polyrun_example.py       run JS, Go, Rust bindings via polyrun
```

Run any example:

```bash
PYTHONPATH=. python3 examples/basic_usage.py
```

---

## Architecture

```
kryptic/
  core.py           Kryptic — run(), batch(), context manager
  pool.py           BrowserPool — asyncio.Queue of Playwright browsers
  context.py        PageContext — full page automation API (50+ methods)
  http_client.py    HttpClient — httpx async client
  sync.py           KrypticSync — synchronous wrapper
  stealth.py        StealthProfile — fingerprint randomisation
  extractors.py     HTML/structured data extraction helpers
  retry.py          @retry, with_retry, RetryConfig
  pipeline.py       Pipeline — chainable automation builder
  proxy_pool.py     ProxyPool — proxy rotation
  storage.py        Cookie/localStorage persistence
  mobile.py         Device emulation profiles
  network.py        NetworkMonitor — request/response capture
  utils.py          detect_browsers(), format_duration()
  types.py          TypedDict definitions
  server/app.py     aiohttp JSON REST API server
  __main__.py       CLI entry point

bindings/
  javascript/       Node.js (zero deps)
  java/             Java 11+ (zero deps)
  go/               Go (zero deps)
  rust/             Rust (ureq + serde_json)
  c/                C (libcurl)
  cpp/              C++17 (libcurl + nlohmann/json)
  php/              PHP 7.4+ (ext-curl)
  ruby/             Ruby 2.7+ (zero deps)
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
