"""Repair flows for disabled source entities.

The hub reads entities, never registries: a registry entry that is disabled never
gets a state, so the hub discovers it as a candidate and can never resolve a value
from it. Telling the user is only half a fix, so the issues are fixable and this
flow enables the entities through the entity registry - the same write the switch
on the entity page performs, with the user's explicit choice.

A fixable issue gets no Ignore button from Home Assistant: its dialog is the
flow, so the flow has to offer it. The first step is therefore a menu, as in the
core integrations that do the same: enable the entities, or ignore the issue.
An ignored issue stays ignored while the hub keeps re-creating it at every
discovery; it only comes back if it is deleted first, i.e. once nothing is
disabled any more and something gets disabled again.
"""

from __future__ import annotations

from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import (
    DOMAIN,
    ISSUE_DISABLED_FALLBACK_ENTITIES,
    ISSUE_DISABLED_SOURCE_ENTITIES,
)

FIXABLE_ISSUES = (
    ISSUE_DISABLED_SOURCE_ENTITIES,
    ISSUE_DISABLED_FALLBACK_ENTITIES,
)


class EnableDisabledEntitiesFlow(RepairsFlow):
    """Enable every entity the issue lists, or ignore the issue."""

    def __init__(self, data: dict[str, str]) -> None:
        self._entity_ids = _split(data.get("entities"))

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Show what would be enabled, with the two choices."""
        placeholders: dict[str, str] = {}
        issue = ir.async_get(self.hass).async_get_issue(DOMAIN, self.issue_id)
        if issue is not None and issue.translation_placeholders:
            placeholders.update(issue.translation_placeholders)
        placeholders["count"] = str(len(self._entity_ids))
        placeholders["entities"] = "\n".join(
            f"- `{entity_id}`" for entity_id in self._entity_ids
        )
        return self.async_show_menu(
            step_id="init",
            menu_options=["confirm", "ignore"],
            description_placeholders=placeholders,
        )

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Enable the entities and finish."""
        registry = er.async_get(self.hass)
        for entity_id in self._entity_ids:
            entry = registry.async_get(entity_id)
            if entry is not None and entry.disabled_by is not None:
                registry.async_update_entity(entity_id, disabled_by=None)
        return self.async_create_entry(data={})

    async def async_step_ignore(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Ignore the issue, the same as Ignore on a non-fixable one."""
        ir.async_ignore_issue(self.hass, DOMAIN, self.issue_id, True)
        return self.async_abort(reason="issue_ignored")


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
