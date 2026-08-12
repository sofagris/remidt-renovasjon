"""Config flow for Renovasjonsportal."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RenovationPortalApi, RenovationPortalConnectionError
from .const import (
    CONF_ADDRESS_ID,
    CONF_ADDRESS_NAME,
    CONF_MUNICIPALITY,
    DOMAIN,
)
from .models import AddressResult, RenovationPortalInvalidResponseError


class RenovationPortalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle configuration of Renovasjonsportal."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize temporary flow state."""
        self._results: dict[str, AddressResult] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user for an address and search the portal."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = RenovationPortalApi(async_get_clientsession(self.hass))
            try:
                results = await api.async_search_addresses(user_input[CONF_ADDRESS])
            except RenovationPortalConnectionError:
                errors["base"] = "cannot_connect"
            except RenovationPortalInvalidResponseError:
                errors["base"] = "invalid_response"
            else:
                if not results:
                    errors["base"] = "no_addresses"
                else:
                    self._results = {result.id: result for result in results}
                    return await self.async_step_select_address()

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                )
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user select one of the address search results."""
        errors: dict[str, str] = {}

        if not self._results:
            return await self.async_step_user()

        if user_input is not None:
            address_id = user_input[CONF_ADDRESS_ID]
            result = self._results.get(address_id)
            if result is None:
                errors["base"] = "invalid_address"
            else:
                api = RenovationPortalApi(async_get_clientsession(self.hass))
                try:
                    await api.async_get_disposals(address_id)
                except RenovationPortalConnectionError:
                    errors["base"] = "cannot_connect"
                except RenovationPortalInvalidResponseError:
                    errors["base"] = "invalid_response"
                else:
                    await self.async_set_unique_id(address_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=result.title,
                        data={
                            CONF_ADDRESS_ID: result.id,
                            CONF_ADDRESS_NAME: result.title,
                            CONF_MUNICIPALITY: result.subtitle,
                        },
                    )

        options = [
            selector.SelectOptionDict(
                value=result.id,
                label=(
                    f"{result.title} – {result.subtitle}"
                    if result.subtitle
                    else result.title
                ),
            )
            for result in self._results.values()
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options)
                )
            }
        )
        return self.async_show_form(
            step_id="select_address",
            data_schema=schema,
            errors=errors,
        )

