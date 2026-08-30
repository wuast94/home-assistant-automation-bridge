from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_COMMAND_TIMEOUT, DOMAIN, PLATFORMS
from .models import BridgeConfigEntry, BridgeData, EntityDefinition
from .registry import BridgeRegistry

CREATE_SCHEMA = vol.Schema({vol.Required("definition"): {
    vol.Required("unique_id"): cv.string, vol.Required("platform"): vol.In(PLATFORMS),
    vol.Required(CONF_NAME): cv.string, vol.Optional("state"): object,
    vol.Optional("attributes", default={}): dict,
    vol.Optional("device_identifier", default="automation-runtime"): cv.string,
    vol.Optional("device_name", default="Automation Runtime"): cv.string,
    vol.Optional("options", default=[]): [cv.string],
    vol.Optional("minimum", default=0.0): vol.Coerce(float),
    vol.Optional("maximum", default=100.0): vol.Coerce(float),
    vol.Optional("step", default=1.0): vol.Coerce(float),
    vol.Optional("command_timeout", default=DEFAULT_COMMAND_TIMEOUT): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
}})
REMOVE_SCHEMA = vol.Schema({vol.Required("unique_id"): cv.string})
RESULT_SCHEMA = vol.Schema({
    vol.Required("correlation_id"): cv.string, vol.Required("success"): cv.boolean,
    vol.Optional("state"): object, vol.Optional("error"): cv.string,
})
STATUS_SCHEMA = vol.Schema({vol.Required("available"): cv.boolean})


def _only_registry(hass: HomeAssistant) -> BridgeRegistry:
    entries = hass.config_entries.async_entries(DOMAIN)
    if len(entries) != 1 or not getattr(entries[0], "runtime_data", None):
        raise HomeAssistantError("The single Automation Bridge config entry is not loaded")
    return entries[0].runtime_data.registry


async def async_setup_entry(hass: HomeAssistant, entry: BridgeConfigEntry) -> bool:
    if len(hass.config_entries.async_entries(DOMAIN)) != 1:
        raise HomeAssistantError("Exactly one Automation Bridge config entry is supported")
    registry = BridgeRegistry(hass)
    await registry.async_load()
    entry.runtime_data = BridgeData(registry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BridgeConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        services = (
            "create_entity", "update_entity", "remove_entity", "command_result", "runtime_status", "list_entities",
        )
        for service in services:
            hass.services.async_remove(DOMAIN, service)
    return unloaded


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "create_entity"):
        return

    async def create(call: ServiceCall) -> None:
        await _only_registry(hass).async_create(EntityDefinition.from_dict(call.data["definition"]))

    async def update(call: ServiceCall) -> None:
        registry = _only_registry(hass)
        incoming = call.data["definition"]
        current = registry.definitions.get(incoming["unique_id"])
        if current is None:
            raise HomeAssistantError(f"Unknown entity: {incoming['unique_id']}")
        await registry.async_update(EntityDefinition.from_dict({**current.as_dict(), **incoming}))

    async def remove(call: ServiceCall) -> None:
        await _only_registry(hass).async_remove(call.data["unique_id"])

    async def command_result(call: ServiceCall) -> None:
        data = dict(call.data)
        correlation_id = data.pop("correlation_id")
        if not _only_registry(hass).resolve_command(correlation_id, data):
            raise HomeAssistantError(f"Unknown or expired correlation id: {correlation_id}")

    async def runtime_status(call: ServiceCall) -> None:
        _only_registry(hass).set_runtime_available(call.data["available"])

    async def list_entities(call: ServiceCall) -> dict[str, Any]:
        return {"entities": [item.as_dict() for item in _only_registry(hass).definitions.values()]}

    hass.services.async_register(DOMAIN, "create_entity", create, schema=CREATE_SCHEMA)
    hass.services.async_register(DOMAIN, "update_entity", update, schema=vol.Schema({vol.Required("definition"): dict}))
    hass.services.async_register(DOMAIN, "remove_entity", remove, schema=REMOVE_SCHEMA)
    hass.services.async_register(DOMAIN, "command_result", command_result, schema=RESULT_SCHEMA)
    hass.services.async_register(DOMAIN, "runtime_status", runtime_status, schema=STATUS_SCHEMA)
    hass.services.async_register(DOMAIN, "list_entities", list_entities, supports_response=SupportsResponse.ONLY)
