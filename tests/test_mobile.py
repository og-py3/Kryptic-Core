"""
Tests for kryptic.mobile device profiles.
"""
import pytest
from kryptic.mobile import get_device, list_devices, context_options, DEVICES


def test_list_devices_returns_sorted_list():
    devices = list_devices()
    assert isinstance(devices, list)
    assert len(devices) >= 5
    assert devices == sorted(devices)


def test_get_iphone_14():
    d = get_device("iPhone 14")
    assert d["is_mobile"] is True
    assert d["has_touch"] is True
    assert d["viewport"]["width"] == 390
    assert d["viewport"]["height"] == 844


def test_get_ipad():
    d = get_device("iPad Air")
    assert d["is_mobile"] is True
    assert d["device_scale_factor"] == 2


def test_get_desktop():
    d = get_device("Desktop 1080p")
    assert d["is_mobile"] is False
    assert d["has_touch"] is False
    assert d["viewport"]["width"] == 1920
    assert d["viewport"]["height"] == 1080


def test_unknown_device_raises():
    with pytest.raises(KeyError, match="Unknown device"):
        get_device("Nonexistent Phone 9000")


def test_context_options_keys():
    opts = context_options("iPhone 14")
    required_keys = {"user_agent", "viewport", "device_scale_factor", "is_mobile", "has_touch"}
    assert required_keys.issubset(opts.keys())


def test_context_options_viewport_dict():
    opts = context_options("Samsung Galaxy S23")
    assert isinstance(opts["viewport"], dict)
    assert "width" in opts["viewport"]
    assert "height" in opts["viewport"]


def test_all_devices_have_required_fields():
    required = {"user_agent", "viewport", "device_scale_factor", "is_mobile", "has_touch"}
    for name, data in DEVICES.items():
        assert required.issubset(data.keys()), f"Device {name!r} missing fields"


def test_get_device_returns_copy():
    d1 = get_device("iPhone 14")
    d2 = get_device("iPhone 14")
    d1["user_agent"] = "modified"
    assert d2["user_agent"] != "modified"


def test_device_scale_factors_positive():
    for name, data in DEVICES.items():
        assert data["device_scale_factor"] > 0, f"{name}: scale factor must be > 0"


def test_all_device_names_in_list():
    names = list_devices()
    for name in DEVICES:
        assert name in names
