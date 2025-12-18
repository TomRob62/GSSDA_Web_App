"""Datetime helpers shared across service modules."""

from __future__ import annotations

import datetime as _dt
from typing import Optional, Union

from Util.timezone_helpers import TimeZoneConverter, get_converter


def to_iso(
    value: Optional[Union[_dt.datetime, str]],
    *,
    timezone: Optional[Union[str, TimeZoneConverter]] = None,
) -> Optional[str]:
    """Return ``value`` serialised to an ISO string using UTC storage."""

    if value is None:
        return None
    converter = get_converter(timezone)
    return converter.to_storage(value)


def ensure_ordered(start: str, end: str) -> None:
    """Raise ``ValueError`` if ``end`` is not after ``start``.

    The helper accepts ISO 8601 strings because the services persist
    timestamps in that representation.
    """

    converter = get_converter()
    start_dt = converter.to_utc(start)
    end_dt = converter.to_utc(end)
    if end_dt <= start_dt:
        raise ValueError("End time must be after start time")
