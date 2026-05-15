"""
Proxy rotation — rotate through a list of proxies across requests.

Run with:  PYTHONPATH=. python3 examples/proxy_rotation.py
"""
import asyncio
from kryptic.proxy_pool import ProxyPool


def main():
    # Example proxy list (replace with real proxies)
    proxies = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080",
    ]

    # ── Round-robin ──────────────────────────────────────────────────────────
    pool = ProxyPool(proxies, strategy="round_robin")
    print("Round-robin:")
    for _ in range(6):
        print(f"  → {pool.next()}")

    # ── Random ───────────────────────────────────────────────────────────────
    pool_rand = ProxyPool(proxies, strategy="random")
    print("\nRandom:")
    for _ in range(6):
        print(f"  → {pool_rand.next()}")

    # ── Mark failures ────────────────────────────────────────────────────────
    pool.mark_failed(proxies[0])
    print(f"\nAfter marking {proxies[0]} as failed:")
    print(f"  Available: {pool.available_count}/{pool.total}")
    for _ in range(4):
        print(f"  → {pool.next()}")

    print("\nUsage with Kryptic:")
    print("  async with Kryptic(proxy=pool.next()) as k:")
    print("      result = await k.run(my_task)")


if __name__ == "__main__":
    main()
