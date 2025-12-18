"""
API routes for Room resources.

Defines endpoints for CRUD operations and list retrieval. All routes
require authentication via bearer token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path, Body, status

from DAL import schemas
from Services import auth as auth_service
from Services import permissions
from Controllers import rooms_controller


router = APIRouter(prefix="/rooms")

@router.post(
    "",
    response_model=schemas.RoomOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    payload: schemas.RoomCreate,
    user=Depends(permissions.require_write_access),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Create a new room. Requires authentication."""
    return rooms_controller.create_room_controller(payload, timezone=timezone)


@router.get("", response_model=schemas.PaginatedResponse)
async def list_rooms(
    user=Depends(auth_service.get_current_user),
    q: str | None = Query(None),
    sort: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    start_time_from: str | None = Query(None),
    start_time_to: str | None = Query(None),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """List rooms with optional search and pagination."""
    return rooms_controller.list_rooms_controller(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        start_time_from=start_time_from,
        start_time_to=start_time_to,
        timezone=timezone,
    )


@router.get("/{room_id:int}", response_model=schemas.RoomOut)
async def get_room(
    room_id: int = Path(..., ge=1),
    user=Depends(auth_service.get_current_user),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Retrieve a specific room by its ID."""
    return rooms_controller.get_room_controller(room_id, timezone=timezone)


@router.patch("/{room_id:int}", response_model=schemas.RoomOut)
async def update_room(
    room_id: int = Path(..., ge=1),
    payload: schemas.RoomUpdate = Body(...),
    user=Depends(permissions.require_write_access),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Update a room. Requires authentication."""
    return rooms_controller.update_room_controller(room_id, payload, timezone=timezone)


@router.delete("/{room_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int = Path(..., ge=1),
    cascade: bool = Query(False),
    user=Depends(permissions.require_write_access),
):
    """Delete a room. Supports cascade deletion if requested."""
    rooms_controller.delete_room_controller(room_id, cascade)
    return None
