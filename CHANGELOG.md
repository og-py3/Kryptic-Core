# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

## [0.2.0] — 2026-05-15

### Added

- `KrypticSync` — fully synchronous wrapper so you never need asyncio
- `StealthProfile` — randomise UA, viewport, locale, timezone, inject anti-bot JS (levels: low / medium / high)
- `Pipeline` — chainable fluent builder: `.goto().click().fill().extract().screenshot().run()`
- `NetworkMonitor` — capture, filter, and analyse all page network requests
- `extractors` module — `extract_links`, `extract_images`, `extract_meta`, `extract_headings`, `extract_table`, `extract_emails`, `extract_phones`, `extract_structured_data`, `snapshot`
- `RetryConfig`, `@retry`, `with_retry` — exponential backoff retry for any async task
- `ProxyPool` — round-robin or random proxy rotation with failure tracking
- Storage helpers — `save_cookies`, `load_cookies`, `save_storage_state`, `get/set/clear_local_storage`
- `mobile` module — 9 device profiles (iPhone, Galaxy, Pixel, iPad, Desktop)
- `PageContext` additions — `pdf()`, `emulate_device()`, `infinite_scroll()`, `drag_and_drop()`, `upload_file()`, `double_click()`, `right_click()`, `check()`, `uncheck()`, `count()`, `exists()`, `auto_accept_dialogs()`, `frame()`, `metrics()`, `accessibility_tree()`, `screenshot_element()`
- CLI commands — `scrape`, `screenshot`, `fetch`, `ping`, `snapshot`
- Language bindings — PHP (ext-curl), Ruby (Net::HTTP), joining existing JS, Java, Go, Rust, C, C++
- [polyrun](https://pypi.org/project/polyrun/) integration — run any binding from Python with `JS.run(...)`, `Go.run(...)`, etc.
- Full test suite — 100+ pytest tests across all modules
- 11 new examples

## [0.1.0] — 2024-05-15

### Added

- `Kryptic` class with `browser` and `http` modes
- `BrowserPool` — concurrent pool of Playwright browser instances
- `PageContext` — high-level page automation API
- `HttpClient` — async HTTP client (GET, POST, PUT, DELETE, HEAD, batch)
- `detect_browsers()` — probe installed Playwright browsers
- HTTP server mode (`python -m kryptic serve`) with JSON REST API
- CLI (`python -m kryptic detect`, `python -m kryptic serve`)
- Bindings: JavaScript, Java, Go, Rust, C, C++
- 5 usage examples
