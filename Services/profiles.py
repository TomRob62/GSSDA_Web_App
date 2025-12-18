"""Service helpers for caller profile creation, retrieval, and filtering."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from DAL.db import get_db
from Util.query_helpers import QueryBuilder, apply_pagination, build_order_clause, like_pattern


def _normalize_text(value: Optional[str]) -> Optional[str]:
    """Trim ``value`` and collapse empty strings to ``None``."""

    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    return value


def _row_to_dict(row) -> Dict:
    """Serialise a joined profile/caller row."""

    caller = None
    if row["caller_id"] is not None:
        caller = {
            "id": row["caller_id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "suffix": row["suffix"],
        }
    return {
        "id": row["id"],
        "caller_cuer_id": row["caller_cuer_id"],
        "advertisement": bool(row["advertisement"]),
        "image_path": row["image_path"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "version": 1,
        "caller": caller,
    }


def _fetch_profile(db, *, profile_id: Optional[int] = None, caller_id: Optional[int] = None):
    """Return a single profile row joined with caller metadata."""

    if profile_id is None and caller_id is None:
        raise ValueError("profile_id or caller_id must be provided")
    where = "profiles.id = ?" if profile_id is not None else "profiles.caller_cuer_id = ?"
    value = profile_id if profile_id is not None else caller_id
    row = db.execute(
        """
        SELECT profiles.*, caller_cuers.id AS caller_id, caller_cuers.first_name, caller_cuers.last_name, caller_cuers.suffix
        FROM profiles
        LEFT JOIN caller_cuers ON profiles.caller_cuer_id = caller_cuers.id
        WHERE {where}
        """.format(where=where),
        (value,),
    ).fetchone()
    return row


def _ensure_caller_exists(db, caller_id: Optional[int]) -> None:
    if caller_id is None:
        return
    caller = db.execute(
        "SELECT id FROM caller_cuers WHERE id = ?",
        (caller_id,),
    ).fetchone()
    if not caller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caller/Cuer not found")


def _guard_unique_profile(db, caller_id: Optional[int], *, exclude_profile_id: Optional[int] = None) -> None:
    if caller_id is None:
        return
    params: List[int] = [caller_id]
    query = "SELECT id FROM profiles WHERE caller_cuer_id = ?"
    if exclude_profile_id is not None:
        query += " AND id <> ?"
        params.append(exclude_profile_id)
    existing = db.execute(query, params).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Caller already has a profile",
        )


def create_profile(data) -> Dict:
    """Persist a new profile for the provided caller."""

    is_advertisement = bool(getattr(data, "advertisement", False))
    caller_id = getattr(data, "caller_cuer_id", None)
    with get_db() as db:
        if not is_advertisement and caller_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="caller_cuer_id is required for non-advertisement profiles",
            )
        _ensure_caller_exists(db, caller_id)
        if not is_advertisement:
            _guard_unique_profile(db, caller_id)
        cur = db.execute(
            """
            INSERT INTO profiles (caller_cuer_id, advertisement, image_path, content)
            VALUES (?, ?, ?, ?)
            """,
            (
                caller_id,
                1 if is_advertisement else 0,
                _normalize_text(getattr(data, "image_path", None)),
                _normalize_text(getattr(data, "content", None)),
            ),
        )
        profile_id = cur.lastrowid
        db.commit()
        row = _fetch_profile(db, profile_id=profile_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile creation failed")
    return _row_to_dict(row)


def list_profiles(
    *,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    caller_cuer_id: Optional[int] = None,
    has_image: Optional[bool] = None,
    has_content: Optional[bool] = None,
    advertisement: Optional[bool] = None,
) -> Tuple[List[Dict], int]:
    """Return paginated profiles for list/advanced views."""

    builder = QueryBuilder(
        "SELECT profiles.id FROM profiles "
        "LEFT JOIN caller_cuers ON profiles.caller_cuer_id = caller_cuers.id "
        "WHERE 1=1"
    )
    builder.add_condition("profiles.caller_cuer_id = ?", caller_cuer_id)
    if advertisement is True:
        builder.add_raw_condition("profiles.advertisement = 1")
    elif advertisement is False:
        builder.add_raw_condition("profiles.advertisement = 0")
    search_like = like_pattern(q)
    if search_like:
        builder.add_condition(
            "(caller_cuers.first_name LIKE ? OR caller_cuers.last_name LIKE ? "
            "OR IFNULL(caller_cuers.suffix, '') LIKE ? OR IFNULL(profiles.content, '') LIKE ?)",
            search_like,
            search_like,
            search_like,
            search_like,
        )
    if has_image is True:
        builder.add_raw_condition("profiles.image_path IS NOT NULL AND TRIM(profiles.image_path) <> ''")
    elif has_image is False:
        builder.add_raw_condition("(profiles.image_path IS NULL OR TRIM(profiles.image_path) = '')")
    if has_content is True:
        builder.add_raw_condition("profiles.content IS NOT NULL AND TRIM(profiles.content) <> ''")
    elif has_content is False:
        builder.add_raw_condition("(profiles.content IS NULL OR TRIM(profiles.content) = '')")

    base_query, params = builder.build()
    order_clause = build_order_clause(
        sort,
        allowed={
            "caller": "caller_cuers.last_name COLLATE NOCASE",
            "created_at": "profiles.created_at",
            "updated_at": "profiles.updated_at",
            "advertisement": "profiles.advertisement",
        },
        default="caller_cuers.last_name COLLATE NOCASE",
    )

    with get_db() as db:
        count_query = f"SELECT COUNT(*) FROM ({base_query}) AS sub"
        total = db.execute(count_query, params).fetchone()[0]
        query = base_query + order_clause + " LIMIT ? OFFSET ?"
        query_params, _ = apply_pagination(params, page=page, page_size=page_size)
        cur = db.execute(query, query_params)
        profile_ids = [row[0] for row in cur.fetchall()]
        profiles = []
        for profile_id in profile_ids:
            row = _fetch_profile(db, profile_id=profile_id)
            if row:
                profiles.append(_row_to_dict(row))
    return profiles, total


def get_profile(profile_id: int) -> Dict:
    """Retrieve a profile by its identifier."""

    with get_db() as db:
        row = _fetch_profile(db, profile_id=profile_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return _row_to_dict(row)


def get_profile_by_caller(caller_id: int) -> Dict:
    """Return a profile by the caller/cuer identifier."""

    with get_db() as db:
        row = _fetch_profile(db, caller_id=caller_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return _row_to_dict(row)


def update_profile(profile_id: int, data) -> Dict:
    """Update stored profile attributes."""

    with get_db() as db:
        row = _fetch_profile(db, profile_id=profile_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        payload = data.model_dump(exclude_unset=True)

        current_advertisement = bool(row["advertisement"])
        new_caller_id = payload.get("caller_cuer_id", row["caller_cuer_id"])
        new_advertisement = payload.get("advertisement", current_advertisement)
        if not new_advertisement and new_caller_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="caller_cuer_id is required for non-advertisement profiles",
            )
        _ensure_caller_exists(db, new_caller_id)
        if not new_advertisement:
            _guard_unique_profile(db, new_caller_id, exclude_profile_id=profile_id)

        image_path = payload["image_path"] if "image_path" in payload else row["image_path"]
        content = payload["content"] if "content" in payload else row["content"]
        db.execute(
            """
            UPDATE profiles
            SET caller_cuer_id = ?, advertisement = ?, image_path = ?, content = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                new_caller_id,
                1 if new_advertisement else 0,
                _normalize_text(image_path),
                _normalize_text(content),
                profile_id,
            ),
        )
        db.commit()
        updated = _fetch_profile(db, profile_id=profile_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return _row_to_dict(updated)


def list_advertisement_profiles(*, limit: Optional[int] = None) -> List[Dict]:
    """Return advertisement profiles ordered by most recent update."""

    query = (
        "SELECT profiles.*, caller_cuers.id AS caller_id, caller_cuers.first_name, "
        "caller_cuers.last_name, caller_cuers.suffix "
        "FROM profiles "
        "LEFT JOIN caller_cuers ON profiles.caller_cuer_id = caller_cuers.id "
        "WHERE profiles.advertisement = 1 "
        "ORDER BY profiles.updated_at DESC"
    )
    params: Tuple[object, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_profile(profile_id: int) -> None:
    """Remove a profile from the database."""

    with get_db() as db:
        row = db.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        db.commit()
