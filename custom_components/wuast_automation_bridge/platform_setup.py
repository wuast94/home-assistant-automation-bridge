from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .models import BridgeConfigEntry
from .platforms import ENTITY_FACTORIES


async def async_setup_bridge_platform(
    hass: HomeAssistant,
    entry: BridgeConfigEntry,
    async_add_entities: AddEntitiesCallback,
    platform: str,
) -> None:
    entry.runtime_data.registry.register_platform(platform, async_add_entities, ENTITY_FACTORIES[platform])

