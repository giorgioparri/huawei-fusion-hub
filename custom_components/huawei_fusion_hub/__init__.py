"""Huawei Fusion Hub - aggregates Huawei Solar / FusionSolar / FusionSolarPlus."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceEntryType

from .const import (
    DEVICE_HUB,
    DEVICE_NAMES,
    DOMAIN,
    ISSUE_ENTITY_ID_DRIFT,
    ISSUE_HA_MINIMUM,
    NEXT_MIN_HA_VERSION,
    ha_below_next_minimum,
)
from .coordinator import HubCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # first, so the notice is shown even if the rest of the setup fails
    _async_check_ha_minimum(hass)

    # create the hub device first so sub-devices can reference it via_device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, DEVICE_HUB)},
        name=DEVICE_NAMES[DEVICE_HUB],
        manufacturer="giorgioparri",
        entry_type=DeviceEntryType.SERVICE,
    )

    coordinator = HubCoordinator(hass, entry)
    await coordinator.async_start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_check_entity_id_drift(hass, entry)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


@callback
def _async_check_ha_minimum(hass: HomeAssistant) -> None:
    """Raise a repair on Home Assistant releases the next version will drop.

    HACS offers an update to every installation, but refuses to download it on
    a Home Assistant older than the minimum in hacs.json, so those users could
    never read a notice shipped with that release. This one ships before it:
    the repair stays until Home Assistant is upgraded, and goes away on the
    first start after that.
    """
    if not ha_below_next_minimum(MAJOR_VERSION, MINOR_VERSION):
        ir.async_delete_issue(hass, DOMAIN, ISSUE_HA_MINIMUM)
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_HA_MINIMUM,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_HA_MINIMUM,
        translation_placeholders={
            "version": f"{MAJOR_VERSION}.{MINOR_VERSION}",
            "minimum": ".".join(str(part) for part in NEXT_MIN_HA_VERSION),
        },
        learn_more_url=(
            "https://github.com/giorgioparri/huawei-fusion-hub"
            "#home-assistant-version-support"
        ),
    )


@callback
def _async_check_entity_id_drift(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Raise a repair when a hub entity_id no longer matches its unique_id.

    Every entity this integration creates presets `self.entity_id` to
    `<domain>.<unique_id>`, and that invariant is what everything
    downstream relies on: templates, dashboards, long-term statistics and
    the InfluxDB schema all address the hub by its `hf_hub_*` ids.

    Home Assistant 2026.8 made renaming entity IDs a first-class action in
    the interface and added "Recreate entity IDs" on the device page. The
    latter regenerates the id from the area, device and entity names
    whenever a custom friendly name is set, which drops the `hf_hub_`
    prefix. Neither is undone on restart, so without this check the drift
    is completely silent.

    The registry is read rather than the live entities: it is loaded from
    storage before setup, so it already holds the ids from the previous
    run. On a fresh install it is simply empty here, and no drift is
    reported - which is correct.
    """
    registry = er.async_get(hass)
    drifted = sorted(
        f"{entity.entity_id} (expected {entity.domain}.{entity.unique_id})"
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        if entity.entity_id != f"{entity.domain}.{entity.unique_id}"
    )

    if not drifted:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_ENTITY_ID_DRIFT)
        return

    _LOGGER.warning(
        "%d hub entity id(s) no longer match their unique id: %s",
        len(drifted),
        ", ".join(drifted),
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_ENTITY_ID_DRIFT,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_ENTITY_ID_DRIFT,
        translation_placeholders={
            "count": str(len(drifted)),
            "entities": "\n".join(f"- `{item}`" for item in drifted),
        },
        learn_more_url="https://github.com/giorgioparri/huawei-fusion-hub#entity-ids",
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: HubCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
