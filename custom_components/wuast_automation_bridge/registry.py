from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import PLATFORMS, STORAGE_KEY, STORAGE_VERSION
from .models import EntityDefinition

type AddEntitiesCallback = Callable[[list[Any]], None]


class BridgeRegistry:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.definitions: dict[str, EntityDefinition] = {}
        self.entities: dict[str, Any] = {}
        self.adders: dict[str, AddEntitiesCallback] = {}
        self.pending_commands: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self.runtime_available = False

    async def async_load(self) -> None:
        stored = await self.store.async_load() or {"entities": {}}
        self.definitions = {
            unique_id: EntityDefinition.from_dict(data) for unique_id, data in stored.get("entities", {}).items()
        }

    async def async_save(self) -> None:
        await self.store.async_save({"entities": {key: item.as_dict() for key, item in self.definitions.items()}})

    def register_platform(self, platform: str, adder: AddEntitiesCallback, factory: Callable[..., Any]) -> None:
        self.adders[platform] = adder
        new_entities = []
        for definition in self.definitions.values():
            if definition.platform == platform and definition.unique_id not in self.entities:
                entity = factory(self, definition)
                self.entities[definition.unique_id] = entity
                new_entities.append(entity)
        if new_entities:
            adder(new_entities)

    async def async_create(self, definition: EntityDefinition) -> None:
        if definition.platform not in PLATFORMS:
            raise ValueError(f"Unsupported platform: {definition.platform}")
        existing = self.definitions.get(definition.unique_id)
        if existing is not None and existing.platform != definition.platform:
            raise ValueError("The platform of an existing entity cannot be changed")
        self.definitions[definition.unique_id] = definition
        await self.async_save()
        if existing is not None:
            entity = self.entities.get(definition.unique_id)
            if entity is not None:
                entity.apply_definition(definition)
                return
        if adder := self.adders.get(definition.platform):
            from .platforms import ENTITY_FACTORIES

            entity = ENTITY_FACTORIES[definition.platform](self, definition)
            self.entities[definition.unique_id] = entity
            adder([entity])

    async def async_update(self, definition: EntityDefinition) -> None:
        if definition.unique_id not in self.definitions:
            raise KeyError(definition.unique_id)
        await self.async_create(definition)

    async def async_remove(self, unique_id: str) -> None:
        definition = self.definitions.pop(unique_id, None)
        if definition is None:
            return
        await self.async_save()
        if entity := self.entities.pop(unique_id, None):
            entity_id = entity.entity_id
            if entity_id:
                await entity.async_remove(force_remove=True)
                registry = er.async_get(self.hass)
                if registry.async_get(entity_id):
                    registry.async_remove(entity_id)

    def create_pending_command(self, correlation_id: str) -> asyncio.Future[dict[str, Any]]:
        future = self.hass.loop.create_future()
        self.pending_commands[correlation_id] = future
        return future

    def discard_pending_command(self, correlation_id: str) -> None:
        self.pending_commands.pop(correlation_id, None)

    def resolve_command(self, correlation_id: str, result: dict[str, Any]) -> bool:
        future = self.pending_commands.pop(correlation_id, None)
        if future is None or future.done():
            return False
        future.set_result(result)
        return True

    def set_runtime_available(self, available: bool) -> None:
        self.runtime_available = available
        for entity in self.entities.values():
            if entity.hass is not None and entity.entity_id is not None:
                entity.async_write_ha_state()
