"""Authentication helpers backed by SQLite token storage."""

from __future__ import annotations

import hashlib
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from DAL.db import get_db
from Services import token_store

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Return a SHA256 hash of ``password``."""

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` when ``plain`` hashes to ``hashed``."""

    return hash_password(plain) == hashed


def _get_user_by_username(db, username: str) -> Any:
    """Return the SQLite row for ``username`` if it exists."""

    return db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def _get_user_by_id(db, user_id: int) -> Any:
    """Return the SQLite row for ``user_id`` if present."""

    return db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


async def authenticate_user(username: str, password: str):
    """Return the user row if the credentials are valid."""

    with get_db() as db:
        row = _get_user_by_username(db, username)
        if not row:
            return None
        if not verify_password(password, row["hashed_password"]):
            return None
        return row


def create_token(user_id: int) -> str:
    """Create a new opaque token associated with ``user_id``."""

    return token_store.create_token(user_id)


def revoke_token(token: str) -> None:
    """Remove ``token`` from persistent storage."""

    token_store.delete_token(token)


def _raise_invalid_token(detail: str) -> None:
    """Raise a standardised HTTP 401 error with ``detail``."""

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_token(credentials: Optional[HTTPAuthorizationCredentials]) -> str:
    """Extract the bearer token value from the credentials object."""

    if credentials is None or not credentials.credentials:
        _raise_invalid_token("Missing access token")

    if credentials.scheme.lower() != "bearer":
        _raise_invalid_token("Unsupported authorization scheme")

    return credentials.credentials


def _get_user_from_token(token: str):
    """Return the user associated with ``token`` or raise an error."""

    user_id = token_store.validate_and_refresh(token)
    if user_id is None:
        _raise_invalid_token("Invalid or expired token")

    with get_db() as db:
        user_row = _get_user_by_id(db, user_id)
        if not user_row:
            token_store.delete_token(token)
            _raise_invalid_token("User not found for token")
        return user_row


def get_token_from_credentials(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    """Validate and return the bearer token from ``credentials``."""

    return _extract_token(credentials)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """Dependency that returns the current authenticated user."""

    token = _extract_token(credentials)
    return _get_user_from_token(token)
