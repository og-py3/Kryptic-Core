"""
Network monitor — capture, filter, and analyse all page requests.

Run with:  PYTHONPATH=. python3 examples/network_monitor.py
"""
import asyncio
from kryptic import Kryptic
from kryptic.network import NetworkMonitor


async def main():
    async with Kryptic(headless=True, concurrency=1) as k:

        async def task(page):
            monitor = NetworkMonitor(page)
            await monitor.start()

            await page.goto("https://example.com", wait_until="networkidle")

            summary = monitor.summary()
            log = monitor.log
            slow = monitor.slow_requests(threshold_ms=200)
            doc_requests = monitor.filter(resource_type="document")

            return {
                "summary": summary,
                "total": len(log),
                "slow": [e.to_dict() for e in slow],
                "documents": [e.to_dict() for e in doc_requests],
                "all": [e.to_dict() for e in log],
            }

        data = await k.run(task)

        print("=== Summary ===")
        for k2, v in data["summary"].items():
            print(f"  {k2}: {v}")

        print(f"\n=== All requests ({data['total']}) ===")
        for entry in data["all"]:
            dur = f"{entry['duration_ms']}ms" if entry["duration_ms"] else "pending"
            print(f"  [{entry['resource_type']:12}] {entry['status'] or 'ERR'}  {dur:10}  {entry['url'][:70]}")

        if data["slow"]:
            print("\n=== Slow requests (>200ms) ===")
            for e in data["slow"]:
                print(f"  {e['duration_ms']}ms  {e['url'][:70]}")


asyncio.run(main())
