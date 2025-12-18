"""Caller/Cuer service helpers with consistent query handling."""

from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from DAL.db import get_db
from Services import event_callers as caller_links
from Util.query_helpers import QueryBuilder, apply_pagination, build_order_clause, like_pattern


def create_caller(data) -> dict:
    """Create a caller/cuer record and return it as a dict."""

    dance_str = ",".join(data.dance_types) if data.dance_types else None
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO caller_cuers (first_name, last_name, suffix, mc, dance_types) VALUES (?, ?, ?, ?, ?)",
            (
                data.first_name,
                data.last_name,
                data.suffix,
                1 if data.mc else 0,
                dance_str,
            ),
        )
        caller_id = cur.lastrowid
        db.commit()
        return get_caller(caller_id)


def list_callers(
    *,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    mc: Optional[bool] = None,
    dance_type: Optional[str] = None,
) -> Tuple[List[dict], int]:
    """Return callers matching the provided filters and the total count."""

    builder = QueryBuilder("SELECT * FROM caller_cuers WHERE 1=1")

    search_like = like_pattern(q)
    if search_like:
        builder.add_condition(
            "(first_name LIKE ? OR last_name LIKE ? OR IFNULL(suffix, '') LIKE ?)",
            search_like,
            search_like,
            search_like,
        )

    if mc is not None:
        builder.add_condition("mc = ?", 1 if mc else 0)

    builder.add_condition("dance_types LIKE ?", like_pattern(dance_type))

    base_query, params = builder.build()
    order_clause = build_order_clause(
        sort,
        allowed={
            "first_name": "first_name",
            "last_name": "last_name",
            "created_at": "created_at",
        },
        default="id",
    )

    count_query = f"SELECT COUNT(*) FROM ({base_query}) as sub"
    with get_db() as db:
        total = db.execute(count_query, params).fetchone()[0]
        data_query = base_query + order_clause + " LIMIT ? OFFSET ?"
        data_params, _ = apply_pagination(params, page=page, page_size=page_size)
        cur = db.execute(data_query, data_params)
        callers = [_row_to_dict(row) for row in cur.fetchall()]

    return callers, total


def get_caller(caller_id: int) -> dict:
    """Return a single caller/cuer record by ID."""

    with get_db() as db:
        cur = db.execute("SELECT * FROM caller_cuers WHERE id = ?", (caller_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caller/Cuer not found")
        return _row_to_dict(row)


def update_caller(caller_id: int, data) -> dict:
    """Update a caller/cuer record and return the persisted representation."""

    with get_db() as db:
        cur = db.execute("SELECT * FROM caller_cuers WHERE id = ?", (caller_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caller/Cuer not found")

        first_name = data.first_name if data.first_name is not None else row["first_name"]
        last_name = data.last_name if data.last_name is not None else row["last_name"]
        suffix = data.suffix if data.suffix is not None else row["suffix"]
        mc_flag = data.mc if data.mc is not None else bool(row["mc"])
        dance_types = data.dance_types if data.dance_types is not None else (
            row["dance_types"].split(",") if row["dance_types"] else []
        )
        dance_str = ",".join(dance_types) if dance_types else None
        db.execute(
            "UPDATE caller_cuers SET first_name=?, last_name=?, suffix=?, mc=?, dance_types=?, updated_at=datetime('now') WHERE id=?",
            (first_name, last_name, suffix, 1 if mc_flag else 0, dance_str, caller_id),
        )
        db.commit()
        return get_caller(caller_id)


def delete_caller(caller_id: int, cascade: bool = False) -> None:
    """Delete a caller/cuer record, optionally cascading related data."""

    with get_db() as db:
        cur = db.execute("SELECT * FROM caller_cuers WHERE id = ?", (caller_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caller/Cuer not found")
        ev_cnt = caller_links.count_event_links(db, caller_id)
        mc_cnt = db.execute("SELECT COUNT(*) FROM mcs WHERE caller_cuer_id = ?", (caller_id,)).fetchone()[0]
        if not cascade and (ev_cnt > 0 or mc_cnt > 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete caller with dependent events or MCs without cascade",
            )
        if cascade:
            caller_links.remove_caller_assignments(db, caller_id)
            db.execute("DELETE FROM mcs WHERE caller_cuer_id = ?", (caller_id,))
        db.execute("DELETE FROM caller_cuers WHERE id = ?", (caller_id,))
        db.commit()


def _row_to_dict(row) -> dict:
    """Convert a raw SQLite row into a serialisable dictionary."""

    dance_list = row["dance_types"].split(",") if row["dance_types"] else []
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "suffix": row["suffix"],
        "mc": bool(row["mc"]),
        "dance_types": dance_list,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "version": 1,
    }
