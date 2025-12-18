"""
API routes for MC resources.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path, Body, status

from DAL import schemas
from Services import auth as auth_service
from Services import permissions
from Controllers import mcs_controller


router = APIRouter(prefix="/mcs")


@router.post("", response_model=schemas.MCOut, status_code=status.HTTP_201_CREATED)
async def create_mc(
    payload: schemas.MCCreate,
    user=Depends(permissions.require_write_access),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Create a new MC assignment."""
    return mcs_controller.create_mc_controller(payload, timezone=timezone)


@router.get("", response_model=schemas.PaginatedResponse)
async def list_mcs(
    user=Depends(auth_service.get_current_user),
    q: str | None = Query(None),
    sort: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    room_id: int | None = Query(None),
    caller_cuer_id: int | None = Query(None),
    start_from: str | None = Query(None),
    start_to: str | None = Query(None),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """List MC assignments with optional filters."""
    return mcs_controller.list_mcs_controller(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        room_id=room_id,
        caller_cuer_id=caller_cuer_id,
        start_from=start_from,
        start_to=start_to,
        timezone=timezone,
    )


@router.get("/{mc_id:int}", response_model=schemas.MCOut)
async def get_mc(
    mc_id: int = Path(..., ge=1),
    user=Depends(auth_service.get_current_user),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Retrieve a specific MC assignment."""
    return mcs_controller.get_mc_controller(mc_id, timezone=timezone)


@router.patch("/{mc_id:int}", response_model=schemas.MCOut)
async def update_mc(
    mc_id: int = Path(..., ge=1),
    payload: schemas.MCUpdate = Body(...),
    user=Depends(permissions.require_write_access),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Update an MC assignment."""
    return mcs_controller.update_mc_controller(mc_id, payload, timezone=timezone)


@router.delete("/{mc_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mc(
    mc_id: int = Path(..., ge=1),
    user=Depends(permissions.require_write_access),
):
    """Delete an MC assignment."""
    mcs_controller.delete_mc_controller(mc_id)
    return None
