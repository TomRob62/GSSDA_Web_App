"""Room service functions with shared query-building utilities."""

from __future__ import annotations

import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from DAL.db import get_db
from Util.datetime_helpers import to_iso
from Util.query_helpers import QueryBuilder, apply_pagination, build_order_clause, like_pattern
from Services import room_repository
from Util.timezone_helpers import TimeZoneConverter, get_converter


def create_room(data, *, converter: TimeZoneConverter | None = None) -> dict:
    """Persist a new room along with its descriptions."""

    tz = get_converter(converter)
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO rooms (room_number, static) VALUES (?, ?)",
            (data.room_number, 1 if data.static else 0),
        )
        room_id = cur.lastrowid
        room_repository.replace_room_descriptions(
            db, room_id, data.descriptions, converter=tz
        )
        db.commit()
        return room_repository.load_room_dict(db, room_id, converter=tz)


def list_rooms(
    *,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    static: Optional[bool] = None,
    room_number: Optional[str] = None,
    description: Optional[str] = None,
    start_time_from: Optional[datetime.datetime] = None,
    start_time_to: Optional[datetime.datetime] = None,
    converter: TimeZoneConverter | None = None,
) -> Tuple[List[dict], int]:
    """Return rooms matching the provided filters along with the total count."""

    tz = get_converter(converter)
    builder = QueryBuilder(
        "SELECT DISTINCT rooms.id FROM rooms "
        "LEFT JOIN room_descriptions ON room_descriptions.room_id = rooms.id "
        "WHERE 1=1"
    )

    search_like = like_pattern(q)
    if search_like:
        builder.add_condition(
            "(rooms.room_number LIKE ? OR room_descriptions.description LIKE ?)",
            search_like,
            search_like,
        )

    builder.add_condition("rooms.room_number LIKE ?", like_pattern(room_number))
    builder.add_condition("room_descriptions.description LIKE ?", like_pattern(description))

    if static is not None:
        builder.add_condition("rooms.static = ?", 1 if static else 0)

    builder.add_condition(
        "(room_descriptions.start_time IS NULL OR room_descriptions.start_time >= ?)",
        to_iso(start_time_from, timezone=tz),
    )
    builder.add_condition(
        "(room_descriptions.start_time IS NULL OR room_descriptions.start_time <= ?)",
        to_iso(start_time_to, timezone=tz),
    )

    base_query, params = builder.build()
    order_clause = build_order_clause(
        sort,
        allowed={
            "room_number": "rooms.room_number",
            "created_at": "rooms.created_at",
            "updated_at": "rooms.updated_at",
        },
        default="rooms.id",
    )

    count_query = f"SELECT COUNT(*) FROM ({base_query}) as sub"
    with get_db() as db:
        total = db.execute(count_query, params).fetchone()[0]
        paginated_query = base_query + order_clause + " LIMIT ? OFFSET ?"
        paginated_params, _ = apply_pagination(params, page=page, page_size=page_size)
        cur = db.execute(paginated_query, paginated_params)
        room_ids = [row[0] for row in cur.fetchall()]
        rooms = room_repository.load_rooms_for_ids(db, room_ids, converter=tz)
    return rooms, total


def get_room(room_id: int, *, converter: TimeZoneConverter | None = None) -> dict:
    """Return a room dictionary with nested descriptions."""

    tz = get_converter(converter)
    with get_db() as db:
        return room_repository.load_room_dict(db, room_id, converter=tz)


def update_room(room_id: int, data, *, converter: TimeZoneConverter | None = None) -> dict:
    """Update scalar room fields and optionally replace descriptions."""

    tz = get_converter(converter)
    with get_db() as db:
        if getattr(data, "id", None) is not None and data.id != room_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room ID mismatch between path and payload",
            )

        room = room_repository.fetch_room_row(db, room_id)

        new_room_number = data.room_number if data.room_number is not None else room["room_number"]
        new_static = int(data.static) if data.static is not None else room["static"]
        db.execute(
            "UPDATE rooms SET room_number = ?, static = ?, updated_at = datetime('now') WHERE id = ?",
            (new_room_number, new_static, room_id),
        )

        if data.descriptions is not None:
            room_repository.replace_room_descriptions(
                db, room_id, data.descriptions, converter=tz
            )
        db.commit()
        return room_repository.load_room_dict(db, room_id, converter=tz)


def delete_room(room_id: int, cascade: bool = False) -> None:
    """Delete a room, optionally cascading to dependent records."""

    with get_db() as db:
        room_repository.fetch_room_row(db, room_id)

        n_events = db.execute("SELECT COUNT(*) FROM events WHERE room_id = ?", (room_id,)).fetchone()[0]
        n_mcs = db.execute("SELECT COUNT(*) FROM mcs WHERE room_id = ?", (room_id,)).fetchone()[0]
        if not cascade and (n_events > 0 or n_mcs > 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete room with dependent events or MCs without cascade",
            )
        if cascade:
            db.execute("DELETE FROM events WHERE room_id = ?", (room_id,))
            db.execute("DELETE FROM mcs WHERE room_id = ?", (room_id,))

        db.execute("DELETE FROM room_descriptions WHERE room_id = ?", (room_id,))
        db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        db.commit()
