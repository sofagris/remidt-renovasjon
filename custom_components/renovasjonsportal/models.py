"""Data models and parsing helpers for Renovasjonsportal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


class RenovationPortalInvalidResponseError(Exception):
    """Raised when Renovasjonsportal returns data in an unexpected format."""


@dataclass(frozen=True, slots=True)
class AddressResult:
    """A selectable address returned by the address search."""

    id: str
    title: str
    subtitle: str


@dataclass(frozen=True, slots=True)
class Disposal:
    """A single waste collection item."""

    date: date
    fraction: str


@dataclass(frozen=True, slots=True)
class NextCollection:
    """All waste fractions collected on the next collection date."""

    date: date
    fractions: tuple[str, ...]


def parse_address_results(payload: Any) -> list[AddressResult]:
    """Parse and de-duplicate address search results."""
    if not isinstance(payload, dict):
        raise RenovationPortalInvalidResponseError("Address response is not an object")

    combined: list[Any] = []
    for key in ("searchResults", "alternateSearchResults"):
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise RenovationPortalInvalidResponseError(f"{key} is not a list")
        combined.extend(value)

    results: list[AddressResult] = []
    seen: set[str] = set()
    for item in combined:
        if not isinstance(item, dict):
            continue
        address_id = item.get("id")
        title = item.get("title")
        subtitle = item.get("subTitle", "")
        if not isinstance(address_id, str) or not isinstance(title, str):
            continue
        if not address_id or not title or address_id in seen:
            continue
        results.append(
            AddressResult(
                id=address_id,
                title=title.strip(),
                subtitle=subtitle.strip() if isinstance(subtitle, str) else "",
            )
        )
        seen.add(address_id)

    return results


def parse_disposals(payload: Any) -> list[Disposal]:
    """Parse disposal records returned by the details endpoint."""
    if not isinstance(payload, dict) or not isinstance(
        payload.get("disposals"), list
    ):
        raise RenovationPortalInvalidResponseError(
            "Details response has no disposal list"
        )

    disposals: list[Disposal] = []
    invalid_rows = 0
    for item in payload["disposals"]:
        if not isinstance(item, dict):
            invalid_rows += 1
            continue

        raw_date = item.get("date")
        fraction = item.get("fraction")
        if (
            not isinstance(raw_date, str)
            or not isinstance(fraction, str)
            or not fraction.strip()
        ):
            invalid_rows += 1
            continue

        try:
            collection_date = datetime.fromisoformat(
                raw_date.replace("Z", "+00:00")
            ).date()
        except ValueError:
            invalid_rows += 1
            continue

        disposals.append(Disposal(date=collection_date, fraction=fraction.strip()))

    if payload["disposals"] and not disposals and invalid_rows:
        raise RenovationPortalInvalidResponseError(
            "No valid disposal records in response"
        )

    return sorted(disposals, key=lambda disposal: disposal.date)


def find_next_collection(
    disposals: list[Disposal], today: date
) -> NextCollection | None:
    """Return all unique fractions on the earliest date that is today or later."""
    upcoming = [disposal for disposal in disposals if disposal.date >= today]
    if not upcoming:
        return None

    next_date = min(disposal.date for disposal in upcoming)
    fractions = tuple(
        dict.fromkeys(
            disposal.fraction
            for disposal in upcoming
            if disposal.date == next_date
        )
    )
    return NextCollection(date=next_date, fractions=fractions)
