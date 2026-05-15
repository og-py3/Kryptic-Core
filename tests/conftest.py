"""
Pytest fixtures for Kryptic tests.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator

from kryptic import Kryptic
from kryptic.http_client import HttpClient


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[HttpClient, None]:
    """A ready HttpClient instance."""
    client = HttpClient(concurrency=5, timeout=15)
    await client.init()
    yield client
    await client.close()


@pytest.fixture
async def kryptic_http() -> AsyncGenerator[Kryptic, None]:
    """A Kryptic instance in HTTP mode."""
    async with Kryptic(mode="http", concurrency=5) as k:
        yield k


@pytest.fixture
async def kryptic_browser() -> AsyncGenerator[Kryptic, None]:
    """A Kryptic instance in browser mode (single instance for speed)."""
    async with Kryptic(headless=True, concurrency=1) as k:
        yield k
