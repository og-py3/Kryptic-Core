"""
Mobile device emulation profiles.

    from kryptic.mobile import devices, get_device

    iphone = get_device("iPhone 14")
    # Use in Kryptic:
    async with Kryptic(user_agent=iphone["user_agent"]) as k:
        async def task(page):
            await page.raw.set_viewport_size(iphone["viewport"])
            await page.goto("https://example.com")
            return await page.title()
        await k.run(task)
"""
from typing import Optional


# Viewport, user agent, and device pixel ratio for popular devices
DEVICES: dict[str, dict] = {
    "iPhone SE": {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 375, "height": 667},
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "iPhone 14": {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 390, "height": 844},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "iPhone 14 Pro Max": {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 430, "height": 932},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "Samsung Galaxy S23": {
        "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "viewport": {"width": 360, "height": 780},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "Pixel 7": {
        "user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 915},
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
    },
    "iPad Air": {
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 820, "height": 1180},
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "iPad Pro 12.9": {
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 1024, "height": 1366},
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "Desktop 1080p": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
    "Desktop 4K": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "viewport": {"width": 3840, "height": 2160},
        "device_scale_factor": 2,
        "is_mobile": False,
        "has_touch": False,
    },
}


def get_device(name: str) -> dict:
    """
    Return device settings by name.

    Raises KeyError if the device name is not found.
    Use list_devices() to see all available names.
    """
    if name not in DEVICES:
        raise KeyError(
            f"Unknown device {name!r}. "
            f"Available: {', '.join(sorted(DEVICES))}"
        )
    return DEVICES[name].copy()


def list_devices() -> list[str]:
    """Return all available device names."""
    return sorted(DEVICES.keys())


def context_options(device_name: str) -> dict:
    """
    Return Playwright new_context() kwargs for the given device.

        device_opts = context_options("iPhone 14")
        ctx = await browser.new_context(**device_opts)
    """
    d = get_device(device_name)
    return {
        "user_agent": d["user_agent"],
        "viewport": d["viewport"],
        "device_scale_factor": d["device_scale_factor"],
        "is_mobile": d["is_mobile"],
        "has_touch": d["has_touch"],
    }


# Alias
devices = DEVICES
