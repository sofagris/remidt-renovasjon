"""Sensor platform for Renovasjonsportal."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ADDRESS_ID,
    CONF_ADDRESS_NAME,
    CONF_MUNICIPALITY,
    DOMAIN,
    WEB_URL,
)
from .coordinator import RenovationPortalCoordinator

FRACTION_ICONS = {
    "papir": "mdi:newspaper-variant-multiple",
    "matavfall": "mdi:food-apple",
    "restavfall": "mdi:trash-can",
    "glass og metallemballasje": "mdi:bottle-soda",
    "plastemballasje": "mdi:recycle",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the next collection sensor."""
    coordinator: RenovationPortalCoordinator = entry.runtime_data
    async_add_entities([RenovationPortalNextCollectionSensor(coordinator, entry)])


class RenovationPortalNextCollectionSensor(
    CoordinatorEntity[RenovationPortalCoordinator], SensorEntity
):
    """Represent the next waste collection date and fractions."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_has_entity_name = True
    _attr_translation_key = "next_collection"

    def __init__(
        self,
        coordinator: RenovationPortalCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        address_id = entry.data[CONF_ADDRESS_ID]
        self._attr_unique_id = f"{address_id}_next_collection"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address_id)},
            name=entry.data[CONF_ADDRESS_NAME],
            manufacturer="Renovasjonsportal",
            model=entry.data.get(CONF_MUNICIPALITY) or None,
            configuration_url=WEB_URL,
        )

    @property
    def native_value(self) -> date | None:
        """Return the next collection date."""
        return self.coordinator.data.date if self.coordinator.data else None

    @property
    def icon(self) -> str:
        """Return an icon matching a single fraction, or a generic icon."""
        data = self.coordinator.data
        if data and len(data.fractions) == 1:
            return FRACTION_ICONS.get(
                data.fractions[0].casefold(), "mdi:trash-can-outline"
            )
        return "mdi:trash-can-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the fractions and useful values for templates and automations."""
        data = self.coordinator.data
        if data is None:
            return {
                "avfallstyper": [],
                "avfallstyper_tekst": "",
                "dager_til": None,
            }

        return {
            "avfallstyper": list(data.fractions),
            "avfallstyper_tekst": ", ".join(data.fractions),
            "dager_til": (data.date - dt_util.now().date()).days,
        }
