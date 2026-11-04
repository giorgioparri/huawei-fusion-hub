"""Tests for the device info of the hub's sub-devices.

Standalone, in the same style as test_normalize.py: run with
`python tests/test_device_info.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from huawei_fusion_hub.const import DEVICE_HUB, DEVICE_NAMES, DOMAIN
from huawei_fusion_hub.devices import sub_device_info

HUB_ID = "0123456789abcdef0123456789abcdef"
SUB_DEVICES = sorted(device for device in DEVICE_NAMES if device != DEVICE_HUB)


def test_links_to_the_hub_by_device_id():
    for device in SUB_DEVICES:
        assert sub_device_info(device, HUB_ID)["via_device_id"] == HUB_ID, device


def test_does_not_use_the_deprecated_via_device():
    """Home Assistant rejects device info that sets both."""
    for device in SUB_DEVICES:
        assert "via_device" not in sub_device_info(device, HUB_ID), device


def test_identifies_the_sub_device():
    for device in SUB_DEVICES:
        info = sub_device_info(device, HUB_ID)
        assert info["identifiers"] == {(DOMAIN, device)}, device
        assert info["name"] == DEVICE_NAMES[device], device


def test_the_hub_is_not_a_sub_device_of_itself():
    try:
        sub_device_info(DEVICE_HUB, HUB_ID)
    except ValueError:
        return
    raise AssertionError("the hub device was accepted as its own sub-device")


def _run():
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
        except AssertionError as err:
            failures += 1
            print(f"FAIL {name}: {err}")
        else:
            print(f"PASS {name}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
