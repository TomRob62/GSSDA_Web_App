"""Service helpers for Event CRUD operations backed by SQLite."""

from __future__ import annotations

import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from DAL.db import get_db
from Services import event_callers as caller_links
from Util.datetime_helpers import ensure_ordered, to_iso
from Util.query_helpers import QueryBuilder, apply_pagination, build_order_clause, like_pattern
from Util.timezone_helpers import TimeZoneConverter, get_converter


def _ensure_room_exists(conn, room_id: int) -> None:
    room = conn.execute("SELECT id FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")


def _serialize_dance_types(values: Optional[List[str]]) -> Optional[str]:
    if values is None:
        return None
    filtered = [value for value in values if value]
    return ",".join(filtered) if filtered else None


def create_event(data, *, converter: TimeZoneConverter | None = None) -> dict:
    """Create a new event and return the persisted record as a dict."""

    tz = get_converter(converter)
    caller_ids = caller_links.normalize_caller_ids(data.caller_cuer_ids)
    dance_str = _serialize_dance_types(data.dance_types)
    with get_db() as db:
        _ensure_room_exists(db, data.room_id)
        caller_links.ensure_callers_exist(db, caller_ids)
        cur = db.execute(
            """
            INSERT INTO events (room_id, start, "end", dance_types)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.room_id,
                tz.to_storage(data.start),
                tz.to_storage(data.end),
                dance_str,
            ),
        )
        event_id = cur.lastrowid
        caller_links.replace_event_callers(db, event_id, caller_ids)
        db.commit()
    return get_event(event_id, converter=tz)


def list_events(
    *,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    room_id: Optional[int] = None,
    caller_cuer_id: Optional[int] = None,
    start_from: Optional[datetime.datetime] = None,
    start_to: Optional[datetime.datetime] = None,
    dance_type: Optional[str] = None,
    room_number: Optional[str] = None,
    caller_name: Optional[str] = None,
    start_days: Optional[List[str]] = None,
    converter: TimeZoneConverter | None = None,
) -> Tuple[List[dict], int]:
    """Return a list of events matching filters along with the total count."""

    tz = get_converter(converter)
    builder = QueryBuilder(
        "SELECT DISTINCT events.id FROM events "
        "JOIN rooms ON events.room_id = rooms.id "
        "LEFT JOIN event_callers ON event_callers.event_id = events.id "
        "LEFT JOIN caller_cuers ON caller_cuers.id = event_callers.caller_cuer_id "
        "WHERE 1=1"
    )
    builder.add_condition("events.room_id = ?", room_id)
    builder.add_condition("event_callers.caller_cuer_id = ?", caller_cuer_id)

    room_like = like_pattern(room_number)
    if room_like:
        builder.add_condition("rooms.room_number LIKE ?", room_like)

    caller_like = like_pattern(caller_name)
    if caller_like:
        builder.add_condition(
            "(caller_cuers.first_name LIKE ? OR caller_cuers.last_name LIKE ?)",
            caller_like,
            caller_like,
        )

    search_like = like_pattern(q)
    if search_like:
        builder.add_condition(
            "(events.dance_types LIKE ? OR rooms.room_number LIKE ? "
            "OR caller_cuers.first_name LIKE ? OR caller_cuers.last_name LIKE ?)",
            search_like,
            search_like,
            search_like,
            search_like,
        )

    dance_like = like_pattern(dance_type)
    if dance_like:
        builder.add_condition("events.dance_types LIKE ?", dance_like)

    builder.add_condition("events.start >= ?", to_iso(start_from, timezone=tz))
    builder.add_condition("events.start <= ?", to_iso(start_to, timezone=tz))

    base_query, params = builder.build()
    order_clause = build_order_clause(
        sort,
        allowed={
            "start": "events.start",
            "end": "events.end",
            "created_at": "events.created_at",
        },
        default="events.start",
    )

    use_day_filter = bool(start_days)
    with get_db() as db:
        if use_day_filter:
            query = base_query + order_clause
            cur = db.execute(query, params)
            event_ids = [row[0] for row in cur.fetchall()]
            total = 0  # updated after filtering
        else:
            count_query = f"SELECT COUNT(*) FROM ({base_query}) as sub"
            total = db.execute(count_query, params).fetchone()[0]
            paginated_query = base_query + order_clause + " LIMIT ? OFFSET ?"
            paginated_params, _ = apply_pagination(params, page=page, page_size=page_size)
            cur = db.execute(paginated_query, paginated_params)
            event_ids = [row[0] for row in cur.fetchall()]

    events = [get_event(eid, converter=tz) for eid in event_ids]

    if use_day_filter:
        day_set = set(start_days)
        filtered = [event for event in events if tz.local_day_key(event["start"]) in day_set]
        total = len(filtered)
        start_index = max(page - 1, 0) * page_size
        events = filtered[start_index : start_index + page_size]

    return events, total


def get_event(event_id: int, *, converter: TimeZoneConverter | None = None) -> dict:
    """Retrieve a single event by its primary key."""

    tz = get_converter(converter)
    with get_db() as db:
        row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        caller_ids = caller_links.fetch_caller_ids(db, event_id)
        dance_list = row["dance_types"].split(",") if row["dance_types"] else []
        return {
            "id": row["id"],
            "room_id": row["room_id"],
            "caller_cuer_ids": caller_ids,
            "start": tz.as_user_timezone(row["start"]),
            "end": tz.as_user_timezone(row["end"]),
            "dance_types": dance_list,
            "created_at": tz.as_user_timezone(row["created_at"]),
            "updated_at": tz.as_user_timezone(row["updated_at"]),
            "version": 1,
        }


def update_event(event_id: int, data, *, converter: TimeZoneConverter | None = None) -> dict:
    """Update an existing event and return the updated record."""

    tz = get_converter(converter)
    with get_db() as db:
        row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        current_caller_ids = caller_links.fetch_caller_ids(db, event_id)
        new_room_id = data.room_id if data.room_id is not None else row["room_id"]
        new_caller_ids = (
            caller_links.normalize_caller_ids(data.caller_cuer_ids)
            if data.caller_cuer_ids is not None
            else current_caller_ids
        )
        new_start = to_iso(data.start, timezone=tz) if data.start is not None else row["start"]
        new_end = to_iso(data.end, timezone=tz) if data.end is not None else row["end"]
        new_dance_types = (
            _serialize_dance_types(data.dance_types)
            if data.dance_types is not None
            else row["dance_types"]
        )

        _ensure_room_exists(db, new_room_id)
        caller_links.ensure_callers_exist(db, new_caller_ids)

        try:
            ensure_ordered(new_start, new_end)
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            ) from exc

        db.execute(
            """
            UPDATE events
            SET room_id = ?, start = ?, "end" = ?, dance_types = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (new_room_id, new_start, new_end, new_dance_types, event_id),
        )
        caller_links.replace_event_callers(db, event_id, new_caller_ids)
        db.commit()
    return get_event(event_id, converter=tz)


def delete_event(event_id: int) -> None:
    """Delete an event by ID."""

    with get_db() as db:
        row = db.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        db.commit()

