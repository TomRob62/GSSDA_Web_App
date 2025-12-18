"""Persistent storage utilities for opaque access tokens.

This module encapsulates all database operations related to
authentication tokens. Tokens are stored in the ``auth_tokens`` table
and include ``last_used`` timestamps to support sliding expiration.

The token lifetime is intentionally short (10 minutes) but refreshed on
each successful verification so active users remain logged in while
idle sessions expire quickly. All timestamps are stored in UTC using a
SQLite-compatible format (``YYYY-MM-DD HH:MM:SS``).
"""

from __future__ import annotations

import datetime as _dt
import secrets
import sqlite3
from typing import Optional

from DAL.db import get_db

TOKEN_LIFETIME_SECONDS = 10 * 60  # 10 minutes
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _utcnow() -> _dt.datetime:
    """Return the current UTC timestamp with timezone information."""

    return _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)


def _format_timestamp(value: _dt.datetime) -> str:
    """Format ``value`` for storage in SQLite."""

    return value.strftime(_TIMESTAMP_FORMAT)


def _parse_timestamp(raw: str) -> _dt.datetime:
    """Parse a timestamp stored in SQLite.

    SQLite may return timestamps without timezone or with fractional
    seconds depending on how they were inserted. This helper normalizes
    the string into an aware ``datetime`` in UTC.
    """

    for fmt in (_TIMESTAMP_FORMAT, "%Y-%m-%d %H:%M:%S.%f"):
        try:
            naive = _dt.datetime.strptime(raw, fmt)
            return naive.replace(tzinfo=_dt.timezone.utc)
        except ValueError:
            continue
    # Fallback to ``fromisoformat`` which can handle a wider range of
    # representations. Assume naive values are UTC.
    parsed = _dt.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed.astimezone(_dt.timezone.utc)


def create_token(user_id: int) -> str:
    """Create and persist a new access token for ``user_id``."""

    for _ in range(5):
        token = secrets.token_urlsafe(32)
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO auth_tokens (token, user_id) VALUES (?, ?)",
                    (token, user_id),
                )
            return token
        except sqlite3.IntegrityError:
            # Extremely unlikely token collision; retry with a new token.
            continue
    raise RuntimeError("Unable to generate a unique authentication token")


def delete_token(token: str) -> None:
    """Remove ``token`` from the database."""

    with get_db() as db:
        db.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))


def validate_and_refresh(token: str, *, now: Optional[_dt.datetime] = None) -> Optional[int]:
    """Validate ``token`` and refresh its ``last_used`` timestamp.

    Returns the associated ``user_id`` if the token is still valid.
    Expired tokens are removed from the database and ``None`` is
    returned.
    """

    now = (now or _utcnow()).astimezone(_dt.timezone.utc)
    cutoff = now - _dt.timedelta(seconds=TOKEN_LIFETIME_SECONDS)
    now_str = _format_timestamp(now)

    with get_db() as db:
        row = db.execute(
            "SELECT user_id, last_used FROM auth_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        if row is None:
            return None

        last_used = _parse_timestamp(row["last_used"])
        if last_used <= cutoff:
            db.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            return None

        db.execute(
            "UPDATE auth_tokens SET last_used = ? WHERE token = ?",
            (now_str, token),
        )
        return int(row["user_id"])


def purge_expired_tokens(*, now: Optional[_dt.datetime] = None) -> int:
    """Delete expired tokens and return the number of rows removed."""

    now = (now or _utcnow()).astimezone(_dt.timezone.utc)
    cutoff = now - _dt.timedelta(seconds=TOKEN_LIFETIME_SECONDS)
    cutoff_str = _format_timestamp(cutoff)

    with get_db() as db:
        cursor = db.execute(
            "DELETE FROM auth_tokens WHERE last_used <= ?",
            (cutoff_str,),
        )
        return cursor.rowcount or 0
