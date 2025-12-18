"""Helpers for working with month/day style date filters."""

from __future__ import annotations

import datetime as _dt
from typing import List


_DISPLAY_FORMAT = "%m/%d"
_STORAGE_FORMAT = "%m-%d"


def normalize_month_day(value: str) -> str:
    """Return a canonical ``MM-DD`` representation for ``value``.

    The UI represents days in ``MM/DD`` form (for example ``"10/19"``). This
    helper trims whitespace, validates the structure, and converts the string to
    ``MM-DD`` so it can be compared using SQLite's ``strftime`` helper.
    """

    if value is None:
        raise ValueError("Day filter value cannot be empty")
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("Day filter value cannot be empty")
    try:
        parsed = _dt.datetime.strptime(trimmed, _DISPLAY_FORMAT)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError("Day filter must use MM/DD format (e.g., 10/19)") from exc
    return parsed.strftime(_STORAGE_FORMAT)


def parse_month_day_list(raw: str | None) -> List[str]:
    """Split ``raw`` on commas and normalise each non-empty value.

    Duplicate entries are removed while preserving the original ordering. Empty
    strings are ignored entirely so callers can treat the empty result as
    "no filter".
    """

    if raw is None:
        return []

    seen: set[str] = set()
    results: List[str] = []
    for piece in raw.split(","):
        candidate = piece.strip()
        if not candidate:
            continue
        key = normalize_month_day(candidate)
        if key not in seen:
            seen.add(key)
            results.append(key)
    return results


def display_from_day_key(day_key: str) -> str:
    """Convert an ``MM-DD`` key into the display-friendly ``MM/DD`` form."""

    try:
        parsed = _dt.datetime.strptime(day_key, _STORAGE_FORMAT)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError("Invalid day key") from exc
    return parsed.strftime(_DISPLAY_FORMAT)


def format_day_label(day_key: str, *, count: int) -> str:
    """Return a descriptive label for a filter option."""

    display = display_from_day_key(day_key)
    suffix = "event" if count == 1 else "events"
    return f"{display} ({count} {suffix})"
