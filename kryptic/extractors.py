"""
Data extraction helpers — pull structured data out of a PageContext.

All functions are async and accept a PageContext as their first argument.

    from kryptic.extractors import (
        extract_links, extract_images, extract_text,
        extract_meta, extract_table, extract_structured_data,
        extract_emails, extract_phones,
    )
"""
import re
from typing import Any, Optional

from .context import PageContext


# ── Links ─────────────────────────────────────────────────────────────────────

async def extract_links(
    page: PageContext,
    base_url: Optional[str] = None,
    internal_only: bool = False,
) -> list[dict[str, str]]:
    """
    Extract all <a href> links from the page.

    Returns list of {"text": ..., "href": ..., "title": ...}.
    If internal_only=True, only return links on the same domain as base_url.
    """
    links: list[dict] = await page.evaluate("""
        () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
            text: (a.innerText || a.textContent || '').trim().slice(0, 200),
            href: a.href,
            title: a.title || '',
        }))
    """)

    if internal_only and base_url:
        from urllib.parse import urlparse
        domain = urlparse(base_url).netloc
        links = [l for l in links if urlparse(l["href"]).netloc == domain]

    return links


# ── Images ────────────────────────────────────────────────────────────────────

async def extract_images(page: PageContext) -> list[dict[str, str]]:
    """
    Extract all <img> tags.

    Returns list of {"src": ..., "alt": ..., "width": ..., "height": ...}.
    """
    return await page.evaluate("""
        () => Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src,
            alt: img.alt || '',
            width: img.naturalWidth || img.width || 0,
            height: img.naturalHeight || img.height || 0,
        }))
    """)


# ── Text ──────────────────────────────────────────────────────────────────────

async def extract_text(page: PageContext, selector: str = "body") -> str:
    """Extract all visible text from the page (or a selector subtree)."""
    return await page.evaluate(f"""
        () => {{
            const el = document.querySelector('{selector}');
            return el ? (el.innerText || el.textContent || '').trim() : '';
        }}
    """)


async def extract_headings(page: PageContext) -> dict[str, list[str]]:
    """Extract h1–h6 headings grouped by level."""
    result: dict[str, list[str]] = {}
    for level in range(1, 7):
        tag = f"h{level}"
        texts = await page.evaluate(f"""
            () => Array.from(document.querySelectorAll('{tag}'))
                       .map(el => (el.innerText || el.textContent || '').trim())
        """)
        if texts:
            result[tag] = texts
    return result


# ── Meta ──────────────────────────────────────────────────────────────────────

async def extract_meta(page: PageContext) -> dict[str, str]:
    """
    Extract <meta> tags plus Open Graph and Twitter card data.

    Returns a flat dict like:
        {"description": "...", "og:title": "...", "twitter:card": "..."}
    """
    return await page.evaluate("""
        () => {
            const meta = {};
            document.querySelectorAll('meta').forEach(m => {
                const key = m.getAttribute('name') || m.getAttribute('property') || m.getAttribute('http-equiv');
                const val = m.getAttribute('content');
                if (key && val) meta[key] = val;
            });
            meta['title'] = document.title;
            const canonical = document.querySelector('link[rel="canonical"]');
            if (canonical) meta['canonical'] = canonical.href;
            return meta;
        }
    """)


# ── Tables ────────────────────────────────────────────────────────────────────

async def extract_table(
    page: PageContext,
    selector: str = "table",
) -> list[dict[str, str]]:
    """
    Extract an HTML table to a list of dicts keyed by column header.

    If the table has no <th> headers, columns are numbered col_0, col_1, …
    """
    return await page.evaluate(f"""
        () => {{
            const table = document.querySelector('{selector}');
            if (!table) return [];
            const rows = Array.from(table.querySelectorAll('tr'));
            if (!rows.length) return [];

            const headers = Array.from(rows[0].querySelectorAll('th, td'))
                .map((el, i) => (el.innerText || el.textContent || '').trim() || `col_${{i}}`);

            return rows.slice(1).map(row => {{
                const cells = Array.from(row.querySelectorAll('td, th'))
                    .map(el => (el.innerText || el.textContent || '').trim());
                const obj = {{}};
                headers.forEach((h, i) => {{ obj[h] = cells[i] ?? ''; }});
                return obj;
            }});
        }}
    """)


async def extract_all_tables(page: PageContext) -> list[list[dict[str, str]]]:
    """Extract every table on the page, returning a list of table data."""
    count: int = await page.evaluate("() => document.querySelectorAll('table').length")
    results = []
    for i in range(count):
        data = await page.evaluate(f"""
            () => {{
                const table = document.querySelectorAll('table')[{i}];
                if (!table) return [];
                const rows = Array.from(table.querySelectorAll('tr'));
                if (!rows.length) return [];
                const headers = Array.from(rows[0].querySelectorAll('th, td'))
                    .map((el, j) => (el.innerText || el.textContent || '').trim() || `col_${{j}}`);
                return rows.slice(1).map(row => {{
                    const cells = Array.from(row.querySelectorAll('td, th'))
                        .map(el => (el.innerText || el.textContent || '').trim());
                    const obj = {{}};
                    headers.forEach((h, k) => {{ obj[h] = cells[k] ?? ''; }});
                    return obj;
                }});
            }}
        """)
        results.append(data)
    return results


# ── Structured data ───────────────────────────────────────────────────────────

async def extract_structured_data(page: PageContext) -> list[dict[str, Any]]:
    """
    Extract JSON-LD structured data blocks from the page.
    Returns a list of parsed JSON-LD objects.
    """
    raw: list[str] = await page.evaluate("""
        () => Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                   .map(s => s.textContent || '')
    """)
    import json
    results = []
    for block in raw:
        try:
            results.append(json.loads(block))
        except Exception:
            pass
    return results


# ── Contact info ──────────────────────────────────────────────────────────────

async def extract_emails(page: PageContext) -> list[str]:
    """Extract email addresses from the page text."""
    text = await extract_text(page)
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    return list(set(re.findall(pattern, text)))


async def extract_phones(page: PageContext) -> list[str]:
    """Extract phone numbers from the page text (best-effort, US/international)."""
    text = await extract_text(page)
    pattern = r"(?:\+?\d[\d\s\-().]{7,}\d)"
    return list(set(re.findall(pattern, text)))


# ── Full page snapshot ────────────────────────────────────────────────────────

async def snapshot(page: PageContext) -> dict[str, Any]:
    """
    Return a full structured snapshot of the page:
    title, url, meta, headings, links, images, emails, phones, structured_data.
    """
    title, url = await page.title(), page.url
    meta, headings, links, images, emails, phones, structured = await _gather(
        extract_meta(page),
        extract_headings(page),
        extract_links(page),
        extract_images(page),
        extract_emails(page),
        extract_phones(page),
        extract_structured_data(page),
    )
    return {
        "title": title,
        "url": url,
        "meta": meta,
        "headings": headings,
        "links": links,
        "images": images,
        "emails": emails,
        "phones": phones,
        "structured_data": structured,
    }


async def _gather(*coros: Any) -> tuple:
    import asyncio
    return tuple(await asyncio.gather(*coros))
