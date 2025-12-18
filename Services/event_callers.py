"""Helper functions for managing event/caller assignments."""

from __future__ import annotations

from typing import Iterable, List, Sequence

from fastapi import HTTPException, status


def _dedupe_preserve_order(values: Sequence[int]) -> List[int]:
    seen = set()
    ordered: List[int] = []
    for value in values:
        if value is None:
            continue
        normalized = int(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def normalize_caller_ids(caller_ids: Sequence[int]) -> List[int]:
    """Return caller IDs without ``None`` values or duplicates."""

    normalized = _dedupe_preserve_order(caller_ids)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one caller/cuer must be assigned to an event",
        )
    return normalized


def ensure_callers_exist(conn, caller_ids: Iterable[int]) -> None:
    """Ensure each caller ID exists in the database."""

    ids = list(caller_ids)
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one caller/cuer must be assigned to an event",
        )
    placeholders = ",".join("?" for _ in ids)
    cur = conn.execute(
        f"SELECT id FROM caller_cuers WHERE id IN ({placeholders})",
        ids,
    )
    found = {row["id"] for row in cur.fetchall()}
    missing = [str(cid) for cid in ids if cid not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caller/Cuer not found for id(s): {', '.join(missing)}",
        )


def fetch_caller_ids(conn, event_id: int) -> List[int]:
    """Return caller IDs for ``event_id`` ordered by position."""

    cur = conn.execute(
        """
        SELECT caller_cuer_id
        FROM event_callers
        WHERE event_id = ?
        ORDER BY position, rowid
        """,
        (event_id,),
    )
    return [row["caller_cuer_id"] for row in cur.fetchall()]


def replace_event_callers(conn, event_id: int, caller_ids: Sequence[int]) -> None:
    """Replace caller assignments for ``event_id`` with ``caller_ids``."""

    conn.execute("DELETE FROM event_callers WHERE event_id = ?", (event_id,))
    for position, caller_id in enumerate(caller_ids):
        conn.execute(
            """
            INSERT INTO event_callers (event_id, caller_cuer_id, position)
            VALUES (?, ?, ?)
            """,
            (event_id, caller_id, position),
        )


def count_event_links(conn, caller_id: int) -> int:
    """Return the number of event assignments referencing ``caller_id``."""

    cur = conn.execute(
        "SELECT COUNT(*) FROM event_callers WHERE caller_cuer_id = ?",
        (caller_id,),
    )
    return cur.fetchone()[0]


def remove_caller_assignments(conn, caller_id: int) -> None:
    """Remove caller assignments and clean up orphaned events."""

    conn.execute("DELETE FROM event_callers WHERE caller_cuer_id = ?", (caller_id,))
    # Delete events that no longer have any caller assignments.
    conn.execute(
        """
        DELETE FROM events
        WHERE id IN (
            SELECT events.id
            FROM events
            LEFT JOIN event_callers ON events.id = event_callers.event_id
            GROUP BY events.id
            HAVING COUNT(event_callers.caller_cuer_id) = 0
        )
        """,
    )
