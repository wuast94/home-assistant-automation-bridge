from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.text import TextEntity

from .entity import BridgeEntity


class BridgeSensor(BridgeEntity, SensorEntity):
    @property
    def native_value(self) -> Any:
        return self.definition.state


class BridgeBinarySensor(BridgeEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool | None:
        return None if self.definition.state is None else bool(self.definition.state)


class BridgeSwitch(BridgeEntity, SwitchEntity):
    @property
    def icon(self) -> str:
        return "mdi:lightbulb"

    @property
    def is_on(self) -> bool | None:
        return None if self.definition.state is None else bool(self.definition.state)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_command("turn_on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_command("turn_off")


class BridgeLight(BridgeEntity, LightEntity):
    def __init__(self, registry: Any, definition: Any) -> None:
        super().__init__(registry, definition)
        self._attr_supported_color_modes = {ColorMode.ONOFF, ColorMode.BRIGHTNESS}

    @property
    def is_on(self) -> bool | None:
        return None if self.definition.state is None else bool(self.definition.state)

    @property
    def brightness(self) -> int | None:
        value = self.definition.attributes.get(ATTR_BRIGHTNESS)
        return int(value) if value is not None else None

    @property
    def color_mode(self) -> ColorMode:
        return ColorMode.BRIGHTNESS if self.brightness is not None else ColorMode.ONOFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_command("turn_on", kwargs)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_command("turn_off", kwargs)


class BridgeButton(BridgeEntity, ButtonEntity):
    async def async_press(self) -> None:
        await self.async_command("press")


class BridgeNumber(BridgeEntity, NumberEntity):
    @property
    def native_value(self) -> float | None:
        return None if self.definition.state is None else float(self.definition.state)

    @property
    def native_min_value(self) -> float:
        return self.definition.minimum

    @property
    def native_max_value(self) -> float:
        return self.definition.maximum

    @property
    def native_step(self) -> float:
        return self.definition.step

    async def async_set_native_value(self, value: float) -> None:
        await self.async_command("set_value", value)


class BridgeSelect(BridgeEntity, SelectEntity):
    @property
    def current_option(self) -> str | None:
        return None if self.definition.state is None else str(self.definition.state)

    @property
    def options(self) -> list[str]:
        return self.definition.options

    async def async_select_option(self, option: str) -> None:
        await self.async_command("select_option", option)


class BridgeText(BridgeEntity, TextEntity):
    @property
    def native_value(self) -> str | None:
        return None if self.definition.state is None else str(self.definition.state)

    async def async_set_value(self, value: str) -> None:
        await self.async_command("set_value", value)


ENTITY_FACTORIES = {
    "sensor": BridgeSensor,
    "binary_sensor": BridgeBinarySensor,
    "switch": BridgeSwitch,
    "light": BridgeLight,
    "button": BridgeButton,
    "number": BridgeNumber,
    "select": BridgeSelect,
    "text": BridgeText,
}
