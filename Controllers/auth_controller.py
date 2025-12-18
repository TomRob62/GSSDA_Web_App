"""Controller functions for authentication and session management."""

from __future__ import annotations

from typing import Mapping, Any

from fastapi import HTTPException, status

from DAL import schemas
from Services import auth as auth_service


async def login_controller(credentials: schemas.LoginRequest) -> schemas.Token:
    """Authenticate the provided credentials and return an access token."""
    user_row = await auth_service.authenticate_user(credentials.username, credentials.password)
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_token(user_row["id"])
    return schemas.Token(access_token=token)


def session_controller(user_row: Mapping[str, Any]) -> schemas.UserOut:
    """Return a response model for the authenticated user."""
    return schemas.UserOut(
        id=user_row["id"],
        username=user_row["username"],
        role=user_row["role"],
        created_at=user_row["created_at"],
        updated_at=user_row["updated_at"],
    )


def logout_controller(token: str) -> None:
    """Invalidate the given token by removing it from persistent storage."""
    auth_service.revoke_token(token)
    return None
