"""
Tests for retry utilities.
"""
import asyncio
import pytest
from kryptic.retry import retry, with_retry, RetryExhausted, RetryConfig


@pytest.mark.asyncio
async def test_retry_succeeds_first_try():
    calls = []

    @retry(max_attempts=3)
    async def task():
        calls.append(1)
        return "ok"

    result = await task()
    assert result == "ok"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_try():
    calls = []

    @retry(max_attempts=3, delay=0)
    async def task():
        calls.append(1)
        if len(calls) < 2:
            raise ValueError("not yet")
        return "ok"

    result = await task()
    assert result == "ok"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_retry_exhausted():
    @retry(max_attempts=3, delay=0)
    async def task():
        raise RuntimeError("always fails")

    with pytest.raises(RetryExhausted) as exc_info:
        await task()
    assert exc_info.value.attempts == 3
    assert isinstance(exc_info.value.last_error, RuntimeError)


@pytest.mark.asyncio
async def test_with_retry():
    calls = []

    async def attempt():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("retry me")
        return "done"

    result = await with_retry(attempt, max_attempts=5, delay=0)
    assert result == "done"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_retry_config():
    cfg = RetryConfig(max_attempts=2, delay=0)

    calls = []

    async def task():
        calls.append(1)
        if len(calls) < 2:
            raise ValueError("x")
        return "ok"

    result = await cfg.run(task)
    assert result == "ok"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_retry_only_specific_exceptions():
    @retry(max_attempts=3, delay=0, exceptions=(ValueError,))
    async def task():
        raise TypeError("not retried")

    with pytest.raises(TypeError):
        await task()
