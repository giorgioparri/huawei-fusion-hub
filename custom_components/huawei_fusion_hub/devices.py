"""Device info for the logical devices the hub groups its entities into."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DEVICE_HUB, DEVICE_NAMES, DOMAIN


def sub_device_info(device: str, hub_device_id: str) -> DeviceInfo:
    """Return the device info of a sub-device linked to the hub device.

    The link goes through `via_device_id`, the registry id of the hub device,
    which replaces the deprecated `via_device` identifier tuple (removed in
    Home Assistant 2027.8). Passing both is rejected, so only this one is set.
    """
    if device == DEVICE_HUB:
        raise ValueError("the hub device cannot be a sub-device of itself")
    return DeviceInfo(
        identifiers={(DOMAIN, device)},
        name=DEVICE_NAMES[device],
        manufacturer="giorgioparri",
        model="Aggregated device",
        entry_type=DeviceEntryType.SERVICE,
        via_device_id=hub_device_id,
    )
