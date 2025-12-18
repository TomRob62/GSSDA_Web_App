"""
API routes for Event resources.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Path, Body, status

from DAL import schemas
from Services import auth as auth_service
from Services import permissions
from Controllers import events_controller


router = APIRouter(prefix="/events")


@router.post("", response_model=schemas.EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: schemas.EventCreate,
    user=Depends(permissions.require_write_access),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Create a new event."""
    return events_controller.create_event_controller(payload, timezone=timezone)


@router.get("", response_model=schemas.PaginatedResponse)
async def list_events(
    user=Depends(auth_service.get_current_user),
    q: str | None = Query(None),
    sort: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    room_id: int | None = Query(None),
    caller_cuer_id: int | None = Query(None),
    start_from: str | None = Query(None),
    start_to: str | None = Query(None),
    dance_type: str | None = Query(None),
    room_number: str | None = Query(None),
    caller_name: str | None = Query(None),
    start_day: str | None = Query(None, description="Filter events by month/day (MM/DD)"),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """List events with optional filters."""
    return events_controller.list_events_controller(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        room_id=room_id,
        caller_cuer_id=caller_cuer_id,
        start_from=start_from,
        start_to=start_to,
        dance_type=dance_type,
        room_number=room_number,
        caller_name=caller_name,
        start_day=start_day,
        timezone=timezone,
    )


@router.get("/days", response_model=List[schemas.DayFilterOption])
async def list_event_days(
    user=Depends(auth_service.get_current_user),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Return distinct day values used for filtering event schedules."""

    return events_controller.list_event_days_controller(timezone=timezone)


@router.get("/{event_id:int}", response_model=schemas.EventOut)
async def get_event(
    event_id: int = Path(..., ge=1),
    user=Depends(auth_service.get_current_user),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Retrieve a specific event by ID."""
    return events_controller.get_event_controller(event_id, timezone=timezone)


@router.patch("/{event_id:int}", response_model=schemas.EventOut)
async def update_event(
    event_id: int = Path(..., ge=1),
    payload: schemas.EventUpdate = Body(...),
    user=Depends(permissions.require_write_access),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
):
    """Update an existing event."""
    return events_controller.update_event_controller(event_id, payload, timezone=timezone)


@router.delete("/{event_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int = Path(..., ge=1),
    user=Depends(permissions.require_write_access),
):
    """Delete an event by ID."""
    events_controller.delete_event_controller(event_id)
    return None
