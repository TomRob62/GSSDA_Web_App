"""Utilities for consistent timezone-aware datetime handling."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = ZoneInfo("UTC")


def _normalize_iso_string(value: str) -> str:
    """Return ``value`` in a form compatible with :func:`datetime.fromisoformat`."""

    trimmed = value.strip()
    if trimmed.endswith("Z"):
        return trimmed[:-1] + "+00:00"
    return trimmed


def _parse_datetime(value: Union[str, _dt.datetime]) -> _dt.datetime:
    """Coerce ``value`` into a :class:`datetime.datetime`."""

    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, str):
        if not value:
            raise ValueError("Datetime string cannot be empty")
        normalized = _normalize_iso_string(value)
        return _dt.datetime.fromisoformat(normalized)
    raise TypeError(f"Unsupported datetime value: {value!r}")


@dataclass(frozen=True)
class TimeZoneConverter:
    """Helper responsible for converting datetimes to and from UTC storage."""

    timezone: ZoneInfo

    def ensure_aware(self, value: _dt.datetime) -> _dt.datetime:
        """Attach :attr:`timezone` when ``value`` is naive."""

        if value.tzinfo is None:
            return value.replace(tzinfo=self.timezone)
        return value

    def to_utc(self, value: Union[str, _dt.datetime]) -> _dt.datetime:
        """Convert ``value`` into an aware UTC :class:`datetime`."""

        dt = _parse_datetime(value)
        aware = self.ensure_aware(dt)
        return aware.astimezone(UTC)

    def to_storage(self, value: Union[str, _dt.datetime]) -> str:
        """Return an ISO string suitable for UTC persistence."""

        utc_value = self.to_utc(value)
        iso = utc_value.isoformat()
        if iso.endswith("+00:00"):
            return iso[:-6] + "Z"
        return iso

    def from_storage(self, value: Union[str, _dt.datetime]) -> _dt.datetime:
        """Convert ``value`` retrieved from storage into :attr:`timezone`."""

        dt = _parse_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(self.timezone)

    def as_user_timezone(self, value: Union[str, _dt.datetime]) -> _dt.datetime:
        """Alias for :meth:`from_storage` for clarity at call sites."""

        return self.from_storage(value)

    def local_day_key(self, value: Union[str, _dt.datetime]) -> str:
        """Return the ``MM-DD`` key for ``value`` in :attr:`timezone`."""

        localized = self.as_user_timezone(value)
        return localized.strftime("%m-%d")


def get_converter(timezone: Optional[Union[str, ZoneInfo, TimeZoneConverter]] = None) -> TimeZoneConverter:
    """Return a :class:`TimeZoneConverter` for ``timezone``."""

    if isinstance(timezone, TimeZoneConverter):
        return timezone
    if isinstance(timezone, ZoneInfo):
        return TimeZoneConverter(timezone)
    if timezone is None or timezone == "":
        return TimeZoneConverter(UTC)
    if isinstance(timezone, str):
        try:
            zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {timezone}") from exc
        return TimeZoneConverter(zone)
    raise TypeError(f"Unsupported timezone value: {timezone!r}")


def parse_datetime(value: Union[str, _dt.datetime], *, timezone: Optional[Union[str, ZoneInfo, TimeZoneConverter]] = None) -> _dt.datetime:
    """Parse ``value`` into an aware :class:`datetime` in ``timezone``."""

    converter = get_converter(timezone)
    dt = _parse_datetime(value)
    dt = converter.ensure_aware(dt)
    return dt
