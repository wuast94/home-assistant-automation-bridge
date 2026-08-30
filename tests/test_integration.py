from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wuast_automation_bridge.const import DOMAIN


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_dynamic_sensor_create_update_remove(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    definition = {"unique_id": "test-temperature", "platform": "sensor", "name": "Temperature", "state": 21.5}
    await hass.services.async_call(DOMAIN, "create_entity", {"definition": definition}, blocking=True)
    await hass.services.async_call(DOMAIN, "runtime_status", {"available": True}, blocking=True)
    entity_id = "sensor.automation_runtime_temperature"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "21.5"

    await hass.services.async_call(
        DOMAIN,
        "update_entity",
        {"definition": {"unique_id": "test-temperature", "state": 22.0}},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == "22.0"

    await hass.services.async_call(DOMAIN, "remove_entity", {"unique_id": "test-temperature"}, blocking=True)
    assert hass.states.get(entity_id) is None


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_switch_is_stateful_toggle(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    definition = {"unique_id": "test-switch", "platform": "switch", "name": "Spot", "state": False}
    await hass.services.async_call(DOMAIN, "create_entity", {"definition": definition}, blocking=True)
    await hass.services.async_call(DOMAIN, "runtime_status", {"available": True}, blocking=True)
    state = hass.states.get("switch.automation_runtime_spot")
    assert state is not None
    assert state.state == "off"
    assert state.attributes["icon"] == "mdi:lightbulb"
    assert "device_class" not in state.attributes
