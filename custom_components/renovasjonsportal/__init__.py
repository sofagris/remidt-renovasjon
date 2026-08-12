"""Renovasjonsportal integration for Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import RenovationPortalApi
from .const import DOMAIN, PLATFORMS
from .coordinator import RenovationPortalCoordinator

_WWW_PATH = Path(__file__).parent / "www"
_CARD_URL = f"/{DOMAIN}/renovasjonsportal-card.js"


async def async_setup(hass: HomeAssistant, _config: ConfigType) -> bool:
    """Register frontend files for the Lovelace card."""
    await _async_setup_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renovasjonsportal from a config entry."""
    await _async_setup_frontend(hass)

    api = RenovationPortalApi(async_get_clientsession(hass))
    coordinator = RenovationPortalCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Renovasjonsportal config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve card assets and register the Lovelace module once."""
    if hass.data.setdefault(DOMAIN, {}).get("frontend_registered"):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                f"/{DOMAIN}",
                str(_WWW_PATH),
                False,
            )
        ]
    )
    add_extra_js_url(hass, _CARD_URL)
    hass.data[DOMAIN]["frontend_registered"] = True

