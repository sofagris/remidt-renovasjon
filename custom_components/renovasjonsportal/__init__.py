"""Renovasjonsportal integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RenovationPortalApi
from .const import PLATFORMS
from .coordinator import RenovationPortalCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renovasjonsportal from a config entry."""
    api = RenovationPortalApi(async_get_clientsession(hass))
    coordinator = RenovationPortalCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Renovasjonsportal config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

