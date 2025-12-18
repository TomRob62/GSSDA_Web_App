"""Compose table-friendly export data for each view."""

from __future__ import annotations

from typing import List, Sequence, Tuple

from Services import export_fetch
from Services import export_rows


def collect_table(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
) -> Tuple[str, Sequence[str], List[Sequence[str]]]:
    """Return ``(title, headers, rows)`` for the requested ``view``."""

    records = export_fetch.fetch_all(
        view=view,
        search=search,
        sort=sort,
        filter_field=filter_field,
        filter_value=filter_value,
    )
    view_key = view.lower()

    if view_key == "rooms":
        headers = ["ID", "Room Number", "Static", "Descriptions"]
        rows = [export_rows.room_row(item) for item in records]
        return "Rooms", headers, rows

    if view_key == "caller_cuers":
        headers = ["ID", "First Name", "Last Name", "MC", "Dance Types"]
        rows = [export_rows.caller_row(item) for item in records]
        return "Caller & Cuer", headers, rows

    if view_key == "events":
        rooms = export_fetch.build_rooms_map()
        callers = export_fetch.build_callers_map()
        headers = ["ID", "Room", "Callers/Cuers", "Start", "End", "Dance Types"]
        rows = [export_rows.event_row(item, rooms, callers) for item in records]
        return "Events", headers, rows

    if view_key == "mcs":
        rooms = export_fetch.build_rooms_map()
        callers = export_fetch.build_callers_map()
        headers = ["ID", "Room", "Caller", "Start", "End"]
        rows = [export_rows.mc_row(item, rooms, callers) for item in records]
        return "MC Assignments", headers, rows

    raise ValueError("Unsupported view for export")
