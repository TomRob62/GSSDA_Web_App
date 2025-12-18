"""Authorization helpers for role-based access control."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from Services import auth as auth_service

READ_ONLY_ROLES = {"attendee", "caller"}


def _is_read_only(user) -> bool:
    return user["role"] in READ_ONLY_ROLES


def _ensure_write_access(user) -> None:
    if _is_read_only(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has read-only access",
        )


def user_can_modify(user) -> bool:
    """Return ``True`` when the user is allowed to modify resources."""

    return not _is_read_only(user)


async def require_write_access(user=Depends(auth_service.get_current_user)):
    """Dependency that rejects users without write permissions."""

    _ensure_write_access(user)
    return user
