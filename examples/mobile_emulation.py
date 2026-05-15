"""
Mobile device emulation — browse as iPhone, Android, iPad, etc.

Run with:  PYTHONPATH=. python3 examples/mobile_emulation.py
"""
import asyncio
from kryptic import Kryptic, list_devices, get_device


async def main():
    print("Available devices:", list_devices(), "\n")

    async with Kryptic(headless=True, concurrency=1) as k:

        for device_name in ["iPhone 14", "Samsung Galaxy S23", "iPad Air"]:
            device = get_device(device_name)

            async def task(page, d=device, name=device_name):
                await page.emulate_device(name)
                await page.block_resources(["image", "stylesheet", "font", "media"])
                await page.goto("https://httpbin.org/user-agent")
                ua = await page.text("pre")
                vp = d["viewport"]
                return {
                    "device": name,
                    "viewport": f"{vp['width']}x{vp['height']}",
                    "is_mobile": d["is_mobile"],
                    "ua_reported": ua[:80],
                }

            result = await k.run(task)
            print(f"Device: {result['device']}")
            print(f"  Viewport  : {result['viewport']}")
            print(f"  Is mobile : {result['is_mobile']}")
            print(f"  UA (first 80): {result['ua_reported']}\n")


asyncio.run(main())
