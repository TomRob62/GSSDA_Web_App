"""Utility helpers for seeding and synchronising default user accounts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from DAL.db import get_db
from Services.auth import hash_password

DEFAULT_ADMIN_USERNAME = "master"
ATTENDEE_USERNAME = "attendee"
CALLER_USERNAME = "caller"


@dataclass
class _SeedUser:
    """Descriptor for default users that must exist in the database."""

    username: str
    password: Optional[str]
    role: str
    require_password: bool = True


def _get_user(db, username: str):
    return db.execute(
        "SELECT id, hashed_password, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def _create_user(db, user: _SeedUser) -> None:
    if user.require_password and not user.password:
        raise RuntimeError(f"Missing password for user '{user.username}'")
    hashed = hash_password(user.password or "")
    db.execute(
        "INSERT OR IGNORE INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
        (user.username, hashed, user.role),
    )


def _ensure_master_user(db) -> None:
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count:
        return
    seed_user = _SeedUser(
        username=DEFAULT_ADMIN_USERNAME,
        password=os.environ.get("INITIAL_ADMIN_PW", "change_me"),
        role="admin",
        require_password=False,
    )
    _create_user(db, seed_user)


def _ensure_attendee_user(db) -> None:
    attendee_password = os.environ.get("ATTENDEE_PASS")
    if not attendee_password:
        raise RuntimeError(
            "ATTENDEE_PASS environment variable must be set for the attendee account"
        )
    existing = _get_user(db, ATTENDEE_USERNAME)
    hashed = hash_password(attendee_password)
    if existing:
        if existing["hashed_password"] != hashed or existing["role"] != "attendee":
            db.execute(
                "UPDATE users SET hashed_password = ?, role = ?, updated_at = datetime('now') WHERE id = ?",
                (hashed, "attendee", existing["id"]),
            )
        return
    db.execute(
        "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
        (ATTENDEE_USERNAME, hashed, "attendee"),
    )


def _ensure_caller_user(db) -> None:
    caller_password = os.environ.get("CALLER_PASS")
    if not caller_password:
        raise RuntimeError(
            "CALLER_PASS environment variable must be set for the caller account"
        )
    existing = _get_user(db, CALLER_USERNAME)
    hashed = hash_password(caller_password)
    if existing:
        if existing["hashed_password"] != hashed or existing["role"] != "caller":
            db.execute(
                "UPDATE users SET hashed_password = ?, role = ?, updated_at = datetime('now') WHERE id = ?",
                (hashed, "caller", existing["id"]),
            )
        return
    db.execute(
        "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
        (CALLER_USERNAME, hashed, "caller"),
    )


def ensure_seed_users() -> None:
    """Ensure the required default users exist and are up to date."""

    with get_db() as db:
        _ensure_master_user(db)
        _ensure_attendee_user(db)
        _ensure_caller_user(db)
