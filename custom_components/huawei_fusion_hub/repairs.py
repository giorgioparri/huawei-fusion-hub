"""Repair flows for disabled source entities.

The hub reads entities, never registries: a registry entry that is disabled never
gets a state, so the hub discovers it as a candidate and can never resolve a value
from it. Telling the user is only half a fix, so the issues are fixable and this
flow enables the entities through the entity registry - the same write the switch
on the entity page performs, with the user's explicit confirmation.
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    ISSUE_DISABLED_FALLBACK_ENTITIES,
    ISSUE_DISABLED_SOURCE_ENTITIES,
)

FIXABLE_ISSUES = (
    ISSUE_DISABLED_SOURCE_ENTITIES,
    ISSUE_DISABLED_FALLBACK_ENTITIES,
)


class EnableDisabledEntitiesFlow(RepairsFlow):
    """Enable every entity the issue lists, after one confirmation."""

    def __init__(self, data: dict[str, str]) -> None:
        self._entity_ids = _split(data.get("entities"))

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Start the fix."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Enable the entities and finish."""
        if user_input is not None:
            registry = er.async_get(self.hass)
            for entity_id in self._entity_ids:
                entry = registry.async_get(entity_id)
                if entry is not None and entry.disabled_by is not None:
                    registry.async_update_entity(entity_id, disabled_by=None)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "count": str(len(self._entity_ids)),
                "entities": "\n".join(
                    f"- `{entity_id}`" for entity_id in self._entity_ids
                ),
            },
        )


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Return the flow for an issue of this integration."""
    if issue_id in FIXABLE_ISSUES:
        return EnableDisabledEntitiesFlow(
            {key: str(value) for key, value in (data or {}).items()}
        )
    return ConfirmRepairFlow()
