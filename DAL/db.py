"""
Lightweight database helper using sqlite3.

This module provides a context manager for obtaining a SQLite
connection and a function to initialize the database schema. It
does not rely on SQLAlchemy; instead, it uses the built‑in
``sqlite3`` module. The database file is stored at
``/home/site/Database/database.db`` and created if it does not exist.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# Determine the absolute path to the database file. Azure Web App Service
# persists data written under ``/home/site`` so we place the SQLite database in
# ``/home/site/Database``.
DB_PATH = Path("/home/site/Database/database.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Context manager yielding a SQLite connection.

    The connection uses ``row_factory=sqlite3.Row`` to return rows as
    dict-like objects. Transactions are committed automatically on
    exit.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db() -> None:
    """Create tables if they do not already exist."""
    with get_db() as db:
        # Users table
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        # Rooms
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT NOT NULL,
                static INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        # Room descriptions
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS room_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                description TEXT,
                start_time TEXT,
                end_time TEXT,
                FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );
            """
        )
        # Caller/Cuer
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS caller_cuers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                suffix TEXT,
                mc INTEGER NOT NULL,
                dance_types TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        # Events
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                start TEXT NOT NULL,
                "end" TEXT NOT NULL,
                dance_types TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE RESTRICT
            );
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS event_callers (
                event_id INTEGER NOT NULL,
                caller_cuer_id INTEGER NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (event_id, caller_cuer_id),
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
                FOREIGN KEY(caller_cuer_id) REFERENCES caller_cuers(id) ON DELETE RESTRICT
            );
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_event_callers_event_id
                ON event_callers(event_id);
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_event_callers_caller_id
                ON event_callers(caller_cuer_id);
            """
        )
        # MCs
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS mcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                caller_cuer_id INTEGER NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE RESTRICT,
                FOREIGN KEY(caller_cuer_id) REFERENCES caller_cuers(id) ON DELETE RESTRICT
            );
            """
        )
        # Caller profiles
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_cuer_id INTEGER,
                advertisement INTEGER NOT NULL DEFAULT 0,
                image_path TEXT,
                content TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(caller_cuer_id) REFERENCES caller_cuers(id) ON DELETE CASCADE
            );
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_profiles_updated_at
                ON profiles(updated_at DESC);
            """
        )
        # Authorization tokens
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_used TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id
                ON auth_tokens(user_id);
            """
        )
        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_auth_tokens_last_used
                ON auth_tokens(last_used);
            """
        )

        _migrate_event_schema(db)
        _migrate_profile_schema(db)


def _migrate_event_schema(db: sqlite3.Connection) -> None:
    """Ensure the events table uses the junction-table structure."""

    info = db.execute("PRAGMA table_info(events)").fetchall()
    if not info:
        return
    column_names = {row[1] for row in info}
    if "caller_cuer_id" not in column_names:
        return

    existing = db.execute(
        "SELECT id, caller_cuer_id FROM events WHERE caller_cuer_id IS NOT NULL"
    ).fetchall()
    for row in existing:
        db.execute(
            """
            INSERT OR IGNORE INTO event_callers (event_id, caller_cuer_id, position)
            VALUES (?, ?, 0)
            """,
            (row["id"], row["caller_cuer_id"]),
        )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS events_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            start TEXT NOT NULL,
            "end" TEXT NOT NULL,
            dance_types TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE RESTRICT
        );
        """
    )
    db.execute(
        """
        INSERT INTO events_new (id, room_id, start, "end", dance_types, created_at, updated_at)
        SELECT id, room_id, start, "end", dance_types, created_at, updated_at
        FROM events;
        """
    )
    db.execute("DROP TABLE events")
    db.execute("ALTER TABLE events_new RENAME TO events")


def _reset_profile_sequence(db: sqlite3.Connection) -> None:
    """Ensure the SQLite autoincrement sequence matches existing profile IDs."""

    try:
        max_id = db.execute("SELECT MAX(id) FROM profiles").fetchone()[0]
    except sqlite3.DatabaseError:
        return
    if max_id is None:
        return
    try:
        db.execute(
            "UPDATE sqlite_sequence SET seq = ? WHERE name = 'profiles'",
            (max_id,),
        )
    except sqlite3.DatabaseError:
        # sqlite_sequence may not exist yet (e.g. clean database)
        pass


def _migrate_profile_schema(db: sqlite3.Connection) -> None:
    """Add advertisement support and relax caller requirements for profiles."""

    info = db.execute("PRAGMA table_info(profiles)").fetchall()
    if not info:
        return

    column_map = {row[1]: row for row in info}
    has_advertisement = "advertisement" in column_map
    caller_not_null = column_map.get("caller_cuer_id", (None, None, None, 0))[3] == 1

    if has_advertisement and not caller_not_null:
        db.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_unique_caller
                ON profiles(caller_cuer_id)
                WHERE advertisement = 0 AND caller_cuer_id IS NOT NULL;
            """
        )
        return

    db.execute("ALTER TABLE profiles RENAME TO profiles_old")
    db.execute(
        """
        CREATE TABLE profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caller_cuer_id INTEGER,
            advertisement INTEGER NOT NULL DEFAULT 0,
            image_path TEXT,
            content TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(caller_cuer_id) REFERENCES caller_cuers(id) ON DELETE CASCADE
        );
        """
    )
    db.execute(
        """
        INSERT INTO profiles (id, caller_cuer_id, advertisement, image_path, content, created_at, updated_at)
        SELECT id, caller_cuer_id, 0, image_path, content, created_at, updated_at
        FROM profiles_old;
        """
    )
    db.execute("DROP TABLE profiles_old")
    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_profiles_updated_at
            ON profiles(updated_at DESC);
        """
    )
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_unique_caller
            ON profiles(caller_cuer_id)
            WHERE advertisement = 0 AND caller_cuer_id IS NOT NULL;
        """
    )
    _reset_profile_sequence(db)
