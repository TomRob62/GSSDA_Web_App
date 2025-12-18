"""
Controller functions for Rooms.

These functions provide a thin layer between the FastAPI routes and the
services. They format responses using Pydantic schemas and wrap
service-level exceptions into standardized error responses.
"""

from __future__ import annotations

import datetime
from typing import List

from fastapi import HTTPException, status

from DAL import schemas
from Services import rooms as room_service
from Util.timezone_helpers import TimeZoneConverter, get_converter, parse_datetime


def _resolve_timezone(value: str | None) -> TimeZoneConverter:
    """Resolve ``value`` into a converter, surfacing invalid zones as HTTP 422."""

    try:
        return get_converter(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _parse_optional_datetime(value: str | None, *, converter: TimeZoneConverter) -> datetime.datetime | None:
    """Convert ``value`` to an aware datetime using ``converter``."""

    if not value:
        return None
    try:
        return parse_datetime(value, timezone=converter)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid datetime format",
        ) from exc


def create_room_controller(
    data: schemas.RoomCreate, *, timezone: str | None = None
) -> schemas.RoomOut:
    """Create a new room via the service and convert to Pydantic schema."""
    tz = _resolve_timezone(timezone)
    room_dict = room_service.create_room(data, converter=tz)
    return convert_room(room_dict)


def list_rooms_controller(
    *,
    q: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 50,
    start_time_from: str | None = None,
    start_time_to: str | None = None,
    timezone: str | None = None,
) -> schemas.PaginatedResponse:
    """Return paginated list of rooms converted to Pydantic models."""
    tz = _resolve_timezone(timezone)
    start_from_dt = _parse_optional_datetime(start_time_from, converter=tz)
    start_to_dt = _parse_optional_datetime(start_time_to, converter=tz)

    rooms, total = room_service.list_rooms(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        start_time_from=start_from_dt,
        start_time_to=start_to_dt,
        converter=tz,
    )
    data = [convert_room(r) for r in rooms]
    return schemas.PaginatedResponse(
        data=data, page=page, page_size=page_size, total=total
    )


def get_room_controller(room_id: int, *, timezone: str | None = None) -> schemas.RoomOut:
    """Return a single room converted to the API schema."""

    tz = _resolve_timezone(timezone)
    room_dict = room_service.get_room(room_id, converter=tz)
    return convert_room(room_dict)


def update_room_controller(
    room_id: int,
    data: schemas.RoomUpdate,
    *,
    timezone: str | None = None,
) -> schemas.RoomOut:
    """Update a room through the service layer and convert the response."""

    tz = _resolve_timezone(timezone)
    room_dict = room_service.update_room(room_id, data, converter=tz)
    return convert_room(room_dict)


def delete_room_controller(room_id: int, cascade: bool = False) -> None:
    """Remove a room, optionally cascading dependent resources."""

    room_service.delete_room(room_id, cascade)


def convert_room(room: dict) -> schemas.RoomOut:
    """Convert a raw room dict with nested description dicts to a Pydantic model."""
    descriptions = [
        schemas.RoomDescriptionOut(
            id=desc["id"],
            description=desc["description"],
            start_time=desc["start_time"],
            end_time=desc["end_time"],
        )
        for desc in room.get("descriptions", [])
    ]
    return schemas.RoomOut(
        id=room["id"],
        room_number=room["room_number"],
        static=room["static"],
        descriptions=descriptions,
        created_at=room["created_at"],
        updated_at=room["updated_at"],
        version=room.get("version", 1),
    )