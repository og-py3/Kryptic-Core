"""
Proxy pool — rotate proxies across requests.

    from kryptic.proxy_pool import ProxyPool
    from kryptic import Kryptic

    proxies = ProxyPool([
        "http://user:pass@proxy1.example.com:8080",
        "http://user:pass@proxy2.example.com:8080",
        "socks5://proxy3.example.com:1080",
    ])

    async with Kryptic(proxy=proxies.next()) as k:
        ...

    # Or use ProxyPool directly with Kryptic for per-task rotation:
    pool = ProxyPool(proxies, strategy="round_robin")
    for url in urls:
        async with Kryptic(proxy=pool.next()) as k:
            result = await k.run(task)
"""
import itertools
import random
from typing import Optional


class ProxyPool:
    """
    Manages a list of proxy URLs and serves them according to a strategy.

    Strategies:
      "round_robin"  — cycle through proxies in order (default)
      "random"       — pick a random proxy each time
    """

    def __init__(
        self,
        proxies: list[str],
        strategy: str = "round_robin",
    ) -> None:
        if not proxies:
            raise ValueError("proxies list cannot be empty")
        if strategy not in ("round_robin", "random"):
            raise ValueError("strategy must be 'round_robin' or 'random'")

        self._proxies = list(proxies)
        self._strategy = strategy
        self._cycle = itertools.cycle(self._proxies)
        self._failed: set[str] = set()

    def next(self) -> str:
        """Return the next proxy URL according to the chosen strategy."""
        available = [p for p in self._proxies if p not in self._failed]
        if not available:
            # All proxies marked failed — reset and try again
            self._failed.clear()
            available = self._proxies[:]

        if self._strategy == "random":
            return random.choice(available)

        # Round-robin: cycle through available proxies
        while True:
            candidate = next(self._cycle)
            if candidate in available:
                return candidate

    def mark_failed(self, proxy: str) -> None:
        """Mark a proxy as failed so it won't be returned by next()."""
        self._failed.add(proxy)

    def mark_recovered(self, proxy: str) -> None:
        """Un-mark a proxy as failed."""
        self._failed.discard(proxy)

    def reset(self) -> None:
        """Clear the failed set and reset the round-robin cycle."""
        self._failed.clear()
        self._cycle = itertools.cycle(self._proxies)

    @property
    def total(self) -> int:
        return len(self._proxies)

    @property
    def available_count(self) -> int:
        return len(self._proxies) - len(self._failed)

    @property
    def failed_count(self) -> int:
        return len(self._failed)

    def __len__(self) -> int:
        return self.total

    def __repr__(self) -> str:
        return (
            f"ProxyPool(total={self.total}, available={self.available_count}, "
            f"strategy={self._strategy!r})"
        )
