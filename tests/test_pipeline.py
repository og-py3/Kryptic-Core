"""
Tests for the Pipeline builder.
"""
import pytest
from kryptic import Kryptic
from kryptic.pipeline import Pipeline


@pytest.mark.asyncio
async def test_pipeline_extract_title():
    async with Kryptic(headless=True, concurrency=1) as k:
        result = await (
            Pipeline(k)
            .block(["image", "stylesheet", "font", "media"])
            .goto("https://example.com")
            .extract("title", "title", method="title")
            .extract("h1", "h1")
            .run()
        )
        assert "Example Domain" in result["title"]
        assert "Example Domain" in result["h1"]


@pytest.mark.asyncio
async def test_pipeline_extract_url():
    async with Kryptic(headless=True, concurrency=1) as k:
        result = await (
            Pipeline(k)
            .block(["image", "stylesheet", "font", "media"])
            .goto("https://example.com")
            .extract("url", "", method="url")
            .run()
        )
        assert "example.com" in result["url"]


@pytest.mark.asyncio
async def test_pipeline_count():
    async with Kryptic(headless=True, concurrency=1) as k:
        result = await (
            Pipeline(k)
            .block(["image", "stylesheet", "font", "media"])
            .goto("https://example.com")
            .extract("link_count", "a[href]", method="count")
            .run()
        )
        assert result["link_count"] >= 1


@pytest.mark.asyncio
async def test_pipeline_evaluate():
    async with Kryptic(headless=True, concurrency=1) as k:
        result = await (
            Pipeline(k)
            .goto("https://example.com")
            .evaluate("doc_title", "() => document.title")
            .run()
        )
        assert isinstance(result["doc_title"], str)
        assert len(result["doc_title"]) > 0


@pytest.mark.asyncio
async def test_pipeline_repr():
    async with Kryptic(headless=True, concurrency=1) as k:
        p = Pipeline(k).goto("https://example.com").extract("t", "h1")
        assert "Pipeline" in repr(p)
        assert "goto" in repr(p)
