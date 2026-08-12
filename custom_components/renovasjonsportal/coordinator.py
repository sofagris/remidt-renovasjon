"""Data coordinator for Renovasjonsportal."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import RenovationPortalApi, RenovationPortalConnectionError
from .const import CONF_ADDRESS_ID, DOMAIN, UPDATE_INTERVAL
from .models import (
    NextCollection,
    RenovationPortalInvalidResponseError,
    find_next_collection,
)

_LOGGER = logging.getLogger(__name__)


class RenovationPortalCoordinator(DataUpdateCoordinator[NextCollection | None]):
    """Fetch and process the collection schedule for one address."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: RenovationPortalApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.data[CONF_ADDRESS_ID]}",
            update_interval=UPDATE_INTERVAL,
        )
        self._api = api
        self._address_id = config_entry.data[CONF_ADDRESS_ID]

    async def _async_update_data(self) -> NextCollection | None:
        """Fetch the next collection from Renovasjonsportal."""
        try:
            disposals = await self._api.async_get_disposals(self._address_id)
        except (
            RenovationPortalConnectionError,
            RenovationPortalInvalidResponseError,
        ) as err:
            raise UpdateFailed(
                "Unable to update the waste collection schedule"
            ) from err

        return find_next_collection(disposals, dt_util.now().date())
