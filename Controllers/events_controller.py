"""Controller functions for Event operations."""

from __future__ import annotations

import datetime
from typing import List

from fastapi import HTTPException, status

from DAL import schemas
from Services import event_filters
from Services import events as event_service
from Util.date_filters import parse_month_day_list
from Util.timezone_helpers import TimeZoneConverter, get_converter, parse_datetime


def _split_dance_types(dance_types) -> List[str]:
    """Ensure dance types are returned as a list."""

    if not dance_types:
        return []
    if isinstance(dance_types, list):
        return dance_types
    return str(dance_types).split(",")


def _convert_event(event: dict) -> schemas.EventOut:
    """Convert raw event dict to Pydantic model."""

    return schemas.EventOut(
        id=event["id"],
        room_id=event["room_id"],
        caller_cuer_ids=event.get("caller_cuer_ids", []),
        start=event["start"],
        end=event["end"],
        dance_types=_split_dance_types(event.get("dance_types")),
        created_at=event["created_at"],
        updated_at=event["updated_at"],
        version=event.get("version", 1),
    )


def _resolve_timezone(value: str | None) -> TimeZoneConverter:
    """Return a converter for ``value`` raising HTTP 422 on error."""

    try:
        return get_converter(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _parse_optional_datetime(value: str | None, *, converter: TimeZoneConverter) -> datetime.datetime | None:
    """Parse an ISO string into a timezone-aware datetime for filters."""

    if not value:
        return None
    try:
        return parse_datetime(value, timezone=converter)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid datetime format",
        ) from exc


def create_event_controller(
    data: schemas.EventCreate, *, timezone: str | None = None
) -> schemas.EventOut:
    """Create an event via the service layer and serialise it."""

    tz = _resolve_timezone(timezone)
    event_dict = event_service.create_event(data, converter=tz)
    return _convert_event(event_dict)


def list_events_controller(
    *,
    q: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 50,
    room_id: int | None = None,
    caller_cuer_id: int | None = None,
    start_from: str | None = None,
    start_to: str | None = None,
    dance_type: str | None = None,
    room_number: str | None = None,
    caller_name: str | None = None,
    start_day: str | None = None,
    timezone: str | None = None,

) -> schemas.PaginatedResponse:
    """Return paginated list of events from the service layer."""

    try:
        day_filters = parse_month_day_list(start_day)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Convert string dates to datetime objects if provided
    tz = _resolve_timezone(timezone)
    sf = _parse_optional_datetime(start_from, converter=tz)
    st = _parse_optional_datetime(start_to, converter=tz)
    events, total = event_service.list_events(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        room_id=room_id,
        caller_cuer_id=caller_cuer_id,
        start_from=sf,
        start_to=st,
        dance_type=dance_type,
        room_number=room_number,
        caller_name=caller_name,
        start_days=day_filters or None,
        converter=tz,
    )
    data = [_convert_event(e) for e in events]
    return schemas.PaginatedResponse(
        data=data, page=page, page_size=page_size, total=total
    )


def get_event_controller(event_id: int, *, timezone: str | None = None) -> schemas.EventOut:
    """Retrieve a single event by ID and convert to schema."""

    tz = _resolve_timezone(timezone)
    event_dict = event_service.get_event(event_id, converter=tz)
    return _convert_event(event_dict)


def update_event_controller(
    event_id: int,
    data: schemas.EventUpdate,
    *,
    timezone: str | None = None,
) -> schemas.EventOut:
    """Update an event and return the schema representation."""

    tz = _resolve_timezone(timezone)
    event_dict = event_service.update_event(event_id, data, converter=tz)
    return _convert_event(event_dict)


def delete_event_controller(event_id: int) -> None:
    """Remove an event by ID."""

    event_service.delete_event(event_id)


def list_event_days_controller(*, timezone: str | None = None) -> List[schemas.DayFilterOption]:
    """Return the available day filters with descriptive metadata."""

    tz = get_converter(timezone)
    options = event_filters.list_event_days(converter=tz)
    return [schemas.DayFilterOption(**option) for option in options]


# Re-export converter for reuse in advanced search controller
convert_event = _convert_event
