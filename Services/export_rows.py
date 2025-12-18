"""Row-formatting helpers for export tables."""

from __future__ import annotations

from typing import Dict, Iterable, Sequence

from Services.export_fetch import format_datetime, format_description


def room_row(item: dict) -> Sequence[str]:
    descriptions = item.get("descriptions", []) or []
    if item.get("static"):
        desc_lines = [desc.get("description", "") for desc in descriptions]
    else:
        desc_lines = [
            format_description(desc.get("start_time"), desc.get("end_time"), desc.get("description"))
            for desc in descriptions
        ]
    description_text = "\n".join(filter(None, desc_lines))
    return [
        str(item.get("id", "")),
        item.get("room_number", ""),
        "Yes" if item.get("static") else "No",
        description_text,
    ]


def caller_row(item: dict) -> Sequence[str]:
    dances = item.get("dance_types") or []
    return [
        str(item.get("id", "")),
        item.get("first_name", ""),
        item.get("last_name", ""),
        "Yes" if item.get("mc") else "No",
        ", ".join(dances),
    ]


def event_row(item: dict, rooms: Dict[int, str], callers: Dict[int, str]) -> Sequence[str]:
    caller_ids: Iterable[int] = item.get("caller_cuer_ids") or []
    caller_labels = [callers.get(cid, f"#{cid}") for cid in caller_ids]
    room_label = rooms.get(item.get("room_id"), str(item.get("room_id", "")))
    return [
        str(item.get("id", "")),
        room_label,
        ", ".join(caller_labels) if caller_labels else "—",
        format_datetime(item.get("start")),
        format_datetime(item.get("end")),
        ", ".join(item.get("dance_types") or []),
    ]


def mc_row(item: dict, rooms: Dict[int, str], callers: Dict[int, str]) -> Sequence[str]:
    room_label = rooms.get(item.get("room_id"), str(item.get("room_id", "")))
    caller_label = callers.get(item.get("caller_cuer_id"), str(item.get("caller_cuer_id", "")))
    return [
        str(item.get("id", "")),
        room_label,
        caller_label,
        format_datetime(item.get("start")),
        format_datetime(item.get("end")),
    ]
