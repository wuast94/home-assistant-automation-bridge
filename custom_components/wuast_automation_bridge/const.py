from __future__ import annotations

from typing import Final

DOMAIN: Final = "wuast_automation_bridge"
PLATFORMS: Final = ("sensor", "binary_sensor", "switch", "light", "button", "number", "select", "text")
STORAGE_KEY: Final = f"{DOMAIN}.entities"
STORAGE_VERSION: Final = 1
EVENT_COMMAND: Final = f"{DOMAIN}_command"
DEFAULT_COMMAND_TIMEOUT: Final = 10.0
