"""Async client for kalender.renovasjonsportal.no."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import aiohttp

from .const import API_BASE_URL, REQUEST_TIMEOUT
from .models import (
    AddressResult,
    Disposal,
    RenovationPortalInvalidResponseError,
    parse_address_results,
    parse_disposals,
)


class RenovationPortalConnectionError(Exception):
    """Raised when Renovasjonsportal cannot be reached."""


class RenovationPortalApi:
    """Client for the public Renovasjonsportal API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client with Home Assistant's shared HTTP session."""
        self._session = session

    async def _async_get_json(self, path: str) -> Any:
        """Get and decode a JSON response."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.get(f"{API_BASE_URL}/{path}") as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise RenovationPortalConnectionError from err
        except (ValueError, TypeError) as err:
            raise RenovationPortalInvalidResponseError(
                "Response is not valid JSON"
            ) from err

    async def async_search_addresses(self, query: str) -> list[AddressResult]:
        """Search for matching addresses."""
        payload = await self._async_get_json(f"address/{quote(query.strip(), safe='')}")
        return parse_address_results(payload)

    async def async_get_disposals(self, address_id: str) -> list[Disposal]:
        """Get the waste collection schedule for an address id."""
        payload = await self._async_get_json(
            f"address/{quote(address_id, safe='')}/details"
        )
        return parse_disposals(payload)
