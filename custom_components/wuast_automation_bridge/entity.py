from __future__ import annotations

import asyncio
import uuid
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, EVENT_COMMAND
from .models import EntityDefinition


class BridgeEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, registry: Any, definition: EntityDefinition) -> None:
        self.registry = registry
        self.definition = definition
        self._attr_unique_id = definition.unique_id
        self._attr_name = definition.name
        self._attr_extra_state_attributes = dict(definition.attributes)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.definition.device_identifier)},
            name=self.definition.device_name,
            manufacturer="Wuast Automation",
            model="External Runtime",
        )

    @property
    def available(self) -> bool:
        return self.registry.runtime_available

    def apply_definition(self, definition: EntityDefinition) -> None:
        self.definition = definition
        self._attr_name = definition.name
        self._attr_extra_state_attributes = dict(definition.attributes)
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_command(self, command: str, value: Any = None) -> None:
        correlation_id = uuid.uuid4().hex
        future = self.registry.create_pending_command(correlation_id)
        self.hass.bus.async_fire(
            EVENT_COMMAND,
            {
                "correlation_id": correlation_id,
                "unique_id": self.definition.unique_id,
                "platform": self.definition.platform,
                "command": command,
                "value": value,
            },
        )
        try:
            result = await asyncio.wait_for(future, timeout=self.definition.command_timeout)
        except TimeoutError as err:
            self.registry.discard_pending_command(correlation_id)
            raise HomeAssistantError(f"Automation runtime timed out for {self.definition.unique_id}") from err
        if not result.get("success", False):
            raise HomeAssistantError(result.get("error") or "Automation runtime rejected the command")
        if "state" in result:
            updated = EntityDefinition.from_dict({**self.definition.as_dict(), "state": result["state"]})
            await self.registry.async_update(updated)

