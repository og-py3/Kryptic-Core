"""
Retry logic — automatically retry failed tasks with exponential backoff.

Run with:  PYTHONPATH=. python3 examples/retry_example.py
"""
import asyncio
from kryptic import Kryptic
from kryptic.retry import retry, with_retry, RetryConfig, RetryExhausted


async def main():
    async with Kryptic(mode="http", concurrency=4) as k:

        # ── 1. @retry decorator ──────────────────────────────────────────────
        print("=== @retry decorator ===")
        call_count = 0

        @retry(max_attempts=4, delay=0.1, backoff=2.0)
        async def flaky_request(http):
            nonlocal call_count
            call_count += 1
            # Simulate flakiness: fail the first 2 attempts
            if call_count < 3:
                raise ConnectionError(f"Simulated failure #{call_count}")
            return await http.get("https://httpbin.org/status/200")

        resp = await k.run(flaky_request)
        print(f"Succeeded on attempt {call_count}: status {resp.status}")

        # ── 2. with_retry() inline ───────────────────────────────────────────
        print("\n=== with_retry() inline ===")
        attempts = 0

        async def task():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TimeoutError("Timed out")
            return await k.run(lambda http: http.get("https://example.com"))

        resp2 = await with_retry(task, max_attempts=3, delay=0.1)
        print(f"Success after {attempts} attempt(s): status {resp2.status}")

        # ── 3. RetryConfig reuse ─────────────────────────────────────────────
        print("\n=== RetryConfig ===")
        cfg = RetryConfig(max_attempts=2, delay=0.1)

        n = 0
        async def another():
            nonlocal n
            n += 1
            if n < 2:
                raise IOError("fail")
            return await k.run(lambda http: http.get("https://example.com"))

        resp3 = await cfg.run(another)
        print(f"RetryConfig succeeded after {n} attempt(s): status {resp3.status}")

        # ── 4. RetryExhausted ────────────────────────────────────────────────
        print("\n=== RetryExhausted ===")
        try:
            @retry(max_attempts=2, delay=0.05)
            async def always_fails(http):
                raise RuntimeError("always broken")

            await k.run(always_fails)
        except RetryExhausted as e:
            print(f"Caught RetryExhausted: {e.attempts} attempts, last: {e.last_error}")


asyncio.run(main())
