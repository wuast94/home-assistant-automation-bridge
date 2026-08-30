from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry


@dataclass(slots=True)
class EntityDefinition:
    unique_id: str
    platform: str
    name: str
    state: Any = None
    attributes: dict[str, Any] = field(default_factory=dict)
    device_identifier: str = "automation-runtime"
    device_name: str = "Automation Runtime"
    options: list[str] = field(default_factory=list)
    minimum: float = 0.0
    maximum: float = 100.0
    step: float = 1.0
    command_timeout: float = 10.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityDefinition:
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def as_dict(self) -> dict[str, Any]:
        return {
            "unique_id": self.unique_id,
            "platform": self.platform,
            "name": self.name,
            "state": self.state,
            "attributes": self.attributes,
            "device_identifier": self.device_identifier,
            "device_name": self.device_name,
            "options": self.options,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "step": self.step,
            "command_timeout": self.command_timeout,
        }


@dataclass(slots=True)
class BridgeData:
    registry: Any


type BridgeConfigEntry = ConfigEntry[BridgeData]
