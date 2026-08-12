"""Renovasjonsportal integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType

from .api import RenovationPortalApi
from .const import DOMAIN, INTEGRATION_VERSION, PLATFORMS, URL_BASE
from .coordinator import RenovationPortalCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_WWW_PATH = Path(__file__).parent / "www"
_CARD_PATH = f"{URL_BASE}/renovasjonsportal-card.js"
_CARD_URL = f"{_CARD_PATH}?v={INTEGRATION_VERSION}"


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
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("frontend_registered"):
        return

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, str(_WWW_PATH), False)]
        )
    except RuntimeError:
        _LOGGER.debug("Static path already registered: %s", URL_BASE)

    domain_data["frontend_registered"] = True

    if hass.is_running:
        await _async_register_lovelace_resource(hass)
    else:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            lambda _event: hass.async_create_task(
                _async_register_lovelace_resource(hass)
            ),
        )


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the card as a Lovelace resource when possible."""
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        _LOGGER.debug("Lovelace unavailable; falling back to frontend extra JS")
        add_extra_js_url(hass, _CARD_URL)
        return

    mode = getattr(lovelace, "mode", None)
    resources = getattr(lovelace, "resources", None)
    if mode != "storage" or resources is None:
        _LOGGER.debug(
            "Lovelace mode %s; falling back to frontend extra JS", mode
        )
        add_extra_js_url(hass, _CARD_URL)
        return

    async def _ensure_registered(_now: Any = None) -> None:
        if not getattr(resources, "loaded", True):
            _LOGGER.debug("Lovelace resources not loaded yet; retrying")
            async_call_later(hass, 5, _ensure_registered)
            return

        existing = [
            item
            for item in resources.async_items()
            if item.get("url", "").split("?", maxsplit=1)[0] == _CARD_PATH
        ]

        if existing:
            current = existing[0]
            if current.get("url") != _CARD_URL:
                _LOGGER.info(
                    "Updating Renovasjonsportal card resource to %s",
                    INTEGRATION_VERSION,
                )
                await resources.async_update_item(
                    current["id"],
                    {"res_type": "module", "url": _CARD_URL},
                )
            return

        _LOGGER.info(
            "Registering Renovasjonsportal card resource %s", INTEGRATION_VERSION
        )
        await resources.async_create_item(
            {"res_type": "module", "url": _CARD_URL}
        )

    await _ensure_registered()
