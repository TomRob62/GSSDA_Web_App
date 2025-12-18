"""Service layer for MC assignments leveraging shared utilities."""

from __future__ import annotations

import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from DAL.db import get_db
from Util.datetime_helpers import ensure_ordered, to_iso
from Util.query_helpers import QueryBuilder, apply_pagination, build_order_clause, like_pattern
from Util.timezone_helpers import TimeZoneConverter, get_converter


def _validate_room_and_mc_caller(room_id: int, caller_id: int) -> None:
    """Ensure the room exists and the caller is configured as an MC."""

    with get_db() as db:
        room = db.execute("SELECT id FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        caller = db.execute(
            "SELECT id, mc FROM caller_cuers WHERE id = ?", (caller_id,),
        ).fetchone()
        if not caller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Caller/Cuer not found"
            )
        if not caller["mc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected caller is not configured as an MC",
            )


def create_mc(data, *, converter: TimeZoneConverter | None = None) -> dict:
    """Create a new MC record and return it as a dict."""

    tz = get_converter(converter)
    _validate_room_and_mc_caller(data.room_id, data.caller_cuer_id)
    with get_db() as db:
        cur = db.execute(
            """
            INSERT INTO mcs (room_id, caller_cuer_id, start, "end")
            VALUES (?, ?, ?, ?)
            """,
            (
                data.room_id,
                data.caller_cuer_id,
                tz.to_storage(data.start),
                tz.to_storage(data.end),
            ),
        )
        mc_id = cur.lastrowid
        db.commit()
        return get_mc(mc_id, converter=tz)


def list_mcs(
    *,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    room_id: Optional[int] = None,
    caller_cuer_id: Optional[int] = None,
    start_from: Optional[datetime.datetime] = None,
    start_to: Optional[datetime.datetime] = None,
    room_number: Optional[str] = None,
    caller_name: Optional[str] = None,
    start_days: Optional[List[str]] = None,
    converter: TimeZoneConverter | None = None,
) -> Tuple[List[dict], int]:
    """List MCs with optional filters and return the total count."""

    tz = get_converter(converter)
    builder = QueryBuilder(
        "SELECT mcs.id FROM mcs "
        "JOIN rooms ON mcs.room_id = rooms.id "
        "JOIN caller_cuers ON mcs.caller_cuer_id = caller_cuers.id "
        "WHERE 1=1"
    )
    builder.add_condition("mcs.room_id = ?", room_id)
    builder.add_condition("mcs.caller_cuer_id = ?", caller_cuer_id)

    search_like = like_pattern(q)
    if search_like:
        builder.add_condition(
            "(rooms.room_number LIKE ? OR caller_cuers.first_name LIKE ? OR caller_cuers.last_name LIKE ?)",
            search_like,
            search_like,
            search_like,
        )

    builder.add_condition("rooms.room_number LIKE ?", like_pattern(room_number))
    caller_like = like_pattern(caller_name)
    if caller_like:
        builder.add_condition(
            "(caller_cuers.first_name LIKE ? OR caller_cuers.last_name LIKE ?)",
            caller_like,
            caller_like,
        )

    builder.add_condition("mcs.start >= ?", to_iso(start_from, timezone=tz))
    builder.add_condition("mcs.start <= ?", to_iso(start_to, timezone=tz))

    base_query, params = builder.build()
    order_clause = build_order_clause(
        sort,
        allowed={
            "start": "mcs.start",
            "end": "mcs.end",
            "created_at": "mcs.created_at",
        },
        default="mcs.start",
    )

    use_day_filter = bool(start_days)
    with get_db() as db:
        if use_day_filter:
            query = base_query + order_clause
            cur = db.execute(query, params)
            mc_ids = [row[0] for row in cur.fetchall()]
            total = 0  # updated after applying the day filter
        else:
            count_query = f"SELECT COUNT(*) FROM ({base_query}) as sub"
            total = db.execute(count_query, params).fetchone()[0]
            paginated_query = base_query + order_clause + " LIMIT ? OFFSET ?"
            paginated_params, _ = apply_pagination(params, page=page, page_size=page_size)
            cur = db.execute(paginated_query, paginated_params)
            mc_ids = [row[0] for row in cur.fetchall()]

    mcs_list = [get_mc(mid, converter=tz) for mid in mc_ids]

    if use_day_filter:
        day_set = set(start_days)
        filtered = [mc for mc in mcs_list if tz.local_day_key(mc["start"]) in day_set]
        total = len(filtered)
        start_index = max(page - 1, 0) * page_size
        mcs_list = filtered[start_index : start_index + page_size]

    return mcs_list, total


def get_mc(mc_id: int, *, converter: TimeZoneConverter | None = None) -> dict:
    """Retrieve a single MC record by ID; raise 404 if missing."""

    tz = get_converter(converter)
    with get_db() as db:
        row = db.execute("SELECT * FROM mcs WHERE id = ?", (mc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MC not found")
        return {
            "id": row["id"],
            "room_id": row["room_id"],
            "caller_cuer_id": row["caller_cuer_id"],
            "start": tz.as_user_timezone(row["start"]),
            "end": tz.as_user_timezone(row["end"]),
            "created_at": tz.as_user_timezone(row["created_at"]),
            "updated_at": tz.as_user_timezone(row["updated_at"]),
            "version": 1,
        }


def update_mc(mc_id: int, data, *, converter: TimeZoneConverter | None = None) -> dict:
    """Update an existing MC assignment."""

    tz = get_converter(converter)
    with get_db() as db:
        row = db.execute("SELECT * FROM mcs WHERE id = ?", (mc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MC not found")
        new_room_id = data.room_id if data.room_id is not None else row["room_id"]
        new_caller_id = (
            data.caller_cuer_id if data.caller_cuer_id is not None else row["caller_cuer_id"]
        )
        new_start = to_iso(data.start, timezone=tz) if data.start is not None else row["start"]
        new_end = to_iso(data.end, timezone=tz) if data.end is not None else row["end"]

        _validate_room_and_mc_caller(new_room_id, new_caller_id)

        try:
            ensure_ordered(new_start, new_end)
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            ) from exc

        db.execute(
            """
            UPDATE mcs
            SET room_id = ?, caller_cuer_id = ?, start = ?, end = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (new_room_id, new_caller_id, new_start, new_end, mc_id),
        )
        db.commit()
    return get_mc(mc_id, converter=tz)


def delete_mc(mc_id: int) -> None:
    """Delete an MC assignment by ID."""

    with get_db() as db:
        row = db.execute("SELECT * FROM mcs WHERE id = ?", (mc_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MC not found")
        db.execute("DELETE FROM mcs WHERE id = ?", (mc_id,))
        db.commit()
