"""Fetch helpers shared by export services."""

from __future__ import annotations

import datetime as _dt
from typing import Dict, List, Optional

from Services import advanced as advanced_service


PAGE_SIZE = 200


def fetch_all(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
) -> List[dict]:
    """Retrieve every record for ``view`` that matches the filters."""

    results: List[dict] = []
    page = 1
    while True:
        items, total = advanced_service.query_resources(
            view=view,
            search=search,
            sort=sort,
            filter_field=filter_field,
            filter_value=filter_value,
            page=page,
            page_size=PAGE_SIZE,
        )
        results.extend(items)
        if len(results) >= total:
            break
        page += 1
    return results


def build_rooms_map() -> Dict[int, str]:
    rooms = fetch_all(view="rooms")
    return {room["id"]: room.get("room_number", "") for room in rooms}


def build_callers_map() -> Dict[int, str]:
    callers = fetch_all(view="caller_cuers")
    result: Dict[int, str] = {}
    for caller in callers:
        suffix = caller.get("suffix") or ""
        suffix_part = f" {suffix}" if suffix else ""
        label = f"{caller.get('first_name', '')} {caller.get('last_name', '')}{suffix_part}".strip()
        result[caller["id"]] = label or f"#{caller['id']}"
    return result


def format_datetime(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        dt = _dt.datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return dt.strftime("%Y-%m-%d %H:%M")


def format_description(start: Optional[str], end: Optional[str], text: Optional[str]) -> str:
    start_label = format_datetime(start)
    end_label = format_datetime(end)
    label = text or ""
    if start_label or end_label:
        range_part = f"{start_label} – {end_label}".strip(" –")
        return f"{range_part}: {label}".strip(" :")
    return label
