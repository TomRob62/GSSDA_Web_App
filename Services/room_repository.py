"""Low-level helpers for loading and mutating room records."""

from __future__ import annotations

from typing import Iterable, List, Mapping, Sequence

import sqlite3

from fastapi import HTTPException, status

from Util.datetime_helpers import to_iso
from Util.timezone_helpers import TimeZoneConverter


def _read_field(source: object, name: str):
    """Return ``name`` from ``source`` supporting both attrs and mapping access."""

    if isinstance(source, Mapping):
        return source.get(name)
    return getattr(source, name, None)


def _ensure_iso(value, *, converter: TimeZoneConverter) -> str | None:
    """Normalise values for storage using UTC serialisation."""

    if value is None:
        return None
    return to_iso(value, timezone=converter)


def fetch_room_row(db: sqlite3.Connection, room_id: int) -> sqlite3.Row:
    """Return the raw SQLite row for ``room_id`` or raise 404."""

    row = db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return row


def fetch_room_descriptions(db: sqlite3.Connection, room_id: int) -> List[sqlite3.Row]:
    """Return all description rows for ``room_id`` ordered by insertion."""

    cur = db.execute(
        "SELECT * FROM room_descriptions WHERE room_id = ? ORDER BY id",
        (room_id,),
    )
    return cur.fetchall()


def build_room_dict(
    room_row: sqlite3.Row,
    description_rows: Sequence[sqlite3.Row],
    *,
    converter: TimeZoneConverter,
) -> dict:
    """Convert raw database rows into the API contract for a room."""

    def _convert_optional(value):
        if value is None:
            return None
        return converter.as_user_timezone(value)

    descriptions = [
        {
            "id": desc["id"],
            "description": desc["description"],
            "start_time": _convert_optional(desc["start_time"]),
            "end_time": _convert_optional(desc["end_time"]),
        }
        for desc in description_rows
    ]
    return {
        "id": room_row["id"],
        "room_number": room_row["room_number"],
        "static": bool(room_row["static"]),
        "descriptions": descriptions,
        "created_at": converter.as_user_timezone(room_row["created_at"]),
        "updated_at": converter.as_user_timezone(room_row["updated_at"]),
        "version": 1,
    }


def load_room_dict(
    db: sqlite3.Connection, room_id: int, *, converter: TimeZoneConverter
) -> dict:
    """Fetch ``room_id`` and return it as a serialized dict."""

    room_row = fetch_room_row(db, room_id)
    description_rows = fetch_room_descriptions(db, room_id)
    return build_room_dict(room_row, description_rows, converter=converter)


def load_rooms_for_ids(
    db: sqlite3.Connection,
    room_ids: Sequence[int],
    *,
    converter: TimeZoneConverter,
) -> List[dict]:
    """Return serialized rooms for each ``room_id`` preserving order."""

    return [load_room_dict(db, room_id, converter=converter) for room_id in room_ids]


def replace_room_descriptions(
    db: sqlite3.Connection,
    room_id: int,
    descriptions: Iterable[object],
    *,
    converter: TimeZoneConverter,
) -> None:
    """Replace all descriptions for ``room_id`` with ``descriptions``."""

    db.execute("DELETE FROM room_descriptions WHERE room_id = ?", (room_id,))
    for desc in descriptions:
        db.execute(
            """
            INSERT INTO room_descriptions (room_id, description, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (
                room_id,
                _read_field(desc, "description"),
                _ensure_iso(_read_field(desc, "start_time"), converter=converter),
                _ensure_iso(_read_field(desc, "end_time"), converter=converter),
            ),
        )
