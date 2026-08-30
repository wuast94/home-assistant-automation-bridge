from .platform_setup import async_setup_bridge_platform


async def async_setup_entry(hass, entry, async_add_entities):
    await async_setup_bridge_platform(hass, entry, async_add_entities, "number")
