"""
API routes for Caller/Cuer resources.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path, Body, status

from DAL import schemas
from Services import auth as auth_service
from Services import permissions
from Controllers import caller_cuers_controller


router = APIRouter(prefix="/caller_cuers")


@router.post("", response_model=schemas.CallerCuerOut, status_code=status.HTTP_201_CREATED)
async def create_caller(
    payload: schemas.CallerCuerCreate,
    user=Depends(permissions.require_write_access),
):
    """Create a new caller/cuer."""
    return caller_cuers_controller.create_caller_controller(payload)


@router.get("", response_model=schemas.PaginatedResponse)
async def list_callers(
    user=Depends(auth_service.get_current_user),
    q: str | None = Query(None),
    sort: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    mc: bool | None = Query(None),
    dance_type: str | None = Query(None),
):
    """List callers/cuers with optional filters and pagination."""
    return caller_cuers_controller.list_callers_controller(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        mc=mc,
        dance_type=dance_type,
    )


@router.get("/{caller_id:int}", response_model=schemas.CallerCuerOut)
async def get_caller(
    caller_id: int = Path(..., ge=1),
    user=Depends(auth_service.get_current_user),
):
    """Retrieve a caller/cuer by ID."""
    return caller_cuers_controller.get_caller_controller(caller_id)


@router.patch("/{caller_id:int}", response_model=schemas.CallerCuerOut)
async def update_caller(
    caller_id: int = Path(..., ge=1),
    payload: schemas.CallerCuerUpdate = Body(...),
    user=Depends(permissions.require_write_access),
):
    """Update a caller/cuer."""
    return caller_cuers_controller.update_caller_controller(caller_id, payload)


@router.delete("/{caller_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_caller(
    caller_id: int = Path(..., ge=1),
    cascade: bool = Query(False),
    user=Depends(permissions.require_write_access),
):
    """Delete a caller/cuer."""
    caller_cuers_controller.delete_caller_controller(caller_id, cascade)
    return None
