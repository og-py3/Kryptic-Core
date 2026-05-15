"""
Retry utilities — wrap async tasks with automatic retries and backoff.

    from kryptic.retry import retry, with_retry

    # Decorator style
    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def scrape(page):
        await page.goto("https://example.com")
        return await page.title()

    # Inline wrapper
    result = await with_retry(
        lambda page: scrape_page(page),
        max_attempts=5,
        delay=0.5,
    )
"""
import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine, Optional, Tuple, Type

logger = logging.getLogger("kryptic.retry")


class RetryExhausted(Exception):
    """Raised when all retry attempts have failed."""
    def __init__(self, attempts: int, last_error: Exception) -> None:
        super().__init__(
            f"All {attempts} attempt(s) failed. Last error: {last_error}"
        )
        self.attempts = attempts
        self.last_error = last_error


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator: retry an async function on failure with exponential backoff.

    Parameters
    ----------
    max_attempts : int
        Total number of attempts (including the first).
    delay : float
        Initial delay in seconds before the first retry.
    backoff : float
        Multiplier applied to delay after each failure.
    jitter : float
        Random fraction of delay to add (avoids thundering herd). 0 = no jitter.
    exceptions : tuple
        Only retry on these exception types.
    on_retry : callable
        Optional callback(attempt_number, exception) called before each retry.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise RetryExhausted(attempt, exc) from exc
                    wait = current_delay
                    if jitter:
                        import random
                        wait += random.uniform(0, jitter * current_delay)
                    logger.debug(
                        f"Attempt {attempt}/{max_attempts} failed: {exc}. "
                        f"Retrying in {wait:.2f}s..."
                    )
                    if on_retry:
                        on_retry(attempt, exc)
                    await asyncio.sleep(wait)
                    current_delay *= backoff
        return wrapper
    return decorator


async def with_retry(
    task: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Any:
    """
    Inline retry wrapper for a task function.

    Useful when you can't use the @retry decorator (e.g. lambdas).

        result = await with_retry(my_task_fn, max_attempts=3)
    """
    current_delay = delay
    for attempt in range(1, max_attempts + 1):
        try:
            return await task()
        except exceptions as exc:
            if attempt == max_attempts:
                raise RetryExhausted(attempt, exc) from exc
            logger.debug(f"Attempt {attempt}/{max_attempts} failed: {exc}. "
                         f"Retrying in {current_delay:.2f}s...")
            await asyncio.sleep(current_delay)
            current_delay *= backoff


class RetryConfig:
    """
    Reusable retry configuration object.

        cfg = RetryConfig(max_attempts=5, delay=0.5, backoff=2)
        result = await cfg.run(my_task_fn)
    """
    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        jitter: float = 0.1,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ) -> None:
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.jitter = jitter
        self.exceptions = exceptions

    async def run(self, task: Callable) -> Any:
        return await with_retry(
            task,
            max_attempts=self.max_attempts,
            delay=self.delay,
            backoff=self.backoff,
            exceptions=self.exceptions,
        )

    def decorator(self) -> Callable:
        return retry(
            max_attempts=self.max_attempts,
            delay=self.delay,
            backoff=self.backoff,
            jitter=self.jitter,
            exceptions=self.exceptions,
        )
