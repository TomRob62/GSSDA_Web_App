"""Service functions powering advanced search across resources."""

from __future__ import annotations

import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from Services import events as events_service
from Services import mcs as mcs_service
from Services import rooms as rooms_service
from Services import caller_cuers as callers_service
from Services import profiles as profiles_service
from Util.timezone_helpers import TimeZoneConverter, get_converter
from Util.date_filters import parse_month_day_list


_BOOL_TRUE = {"true", "1", "yes", "y"}
_BOOL_FALSE = {"false", "0", "no", "n"}


def _coerce_bool(value: Optional[str]) -> Optional[bool]:
    """Interpret ``value`` as a boolean flag when possible."""

    if value is None or value == "":
        return None
    lowered = value.lower()
    if lowered in _BOOL_TRUE:
        return True
    if lowered in _BOOL_FALSE:
        return False
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid boolean filter value",
    )


def _coerce_datetime(value: Optional[str]) -> Optional[datetime.datetime]:
    """Parse ``value`` as an ISO 8601 timestamp."""

    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format",
        ) from exc


def _coerce_int(value: Optional[str]) -> Optional[int]:
    """Convert ``value`` into an :class:`int` when provided."""

    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid numeric filter value",
        ) from exc


def _normalize_sort(sort: Optional[str]) -> Optional[str]:
    """Return a canonical representation for ``sort`` expressions."""

    if not sort:
        return None
    return sort.replace("::", ":").strip()


def query_resources(
    *,
    view: str,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    filter_field: Optional[str] = None,
    filter_value: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    timezone: TimeZoneConverter | str | None = None,
) -> Tuple[List[dict], int]:
    """Dispatch advanced queries to the appropriate service."""

    view_key = view.lower()
    normalized_sort = _normalize_sort(sort)
    tz = get_converter(timezone)

    if view_key == "rooms":
        static_flag = _coerce_bool(filter_value) if filter_field == "static" else None
        room_number = filter_value if filter_field == "room_number" else None
        description = filter_value if filter_field == "description" else None
        start_from = _coerce_datetime(filter_value) if filter_field == "start_from" else None
        start_to = _coerce_datetime(filter_value) if filter_field == "start_to" else None
        return rooms_service.list_rooms(
            q=search,
            sort=normalized_sort,
            page=page,
            page_size=page_size,
            static=static_flag,
            room_number=room_number,
            description=description,
            start_time_from=start_from,
            start_time_to=start_to,
            converter=tz,
        )

    if view_key == "caller_cuers":
        mc_flag = _coerce_bool(filter_value) if filter_field == "mc" else None
        dance_type = filter_value if filter_field == "dance_type" else None
        return callers_service.list_callers(
            q=search,
            sort=normalized_sort,
            page=page,
            page_size=page_size,
            mc=mc_flag,
            dance_type=dance_type,
        )

    if view_key == "events":
        room_id = _coerce_int(filter_value) if filter_field == "room" else None
        caller_id = _coerce_int(filter_value) if filter_field == "caller" else None
        dance_type = filter_value if filter_field == "dance_type" else None
        start_from = _coerce_datetime(filter_value) if filter_field == "start_from" else None
        start_to = _coerce_datetime(filter_value) if filter_field == "start_to" else None
        room_number = filter_value if filter_field == "room_number" else None
        caller_name = filter_value if filter_field == "caller_name" else None
        start_days = None
        if filter_field == "start_day":
            try:
                parsed_days = parse_month_day_list(filter_value)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            start_days = parsed_days or None
        return events_service.list_events(
            q=search,
            sort=normalized_sort,
            page=page,
            page_size=page_size,
            room_id=room_id,
            caller_cuer_id=caller_id,
            start_from=start_from,
            start_to=start_to,
            dance_type=dance_type,
            room_number=room_number,
            caller_name=caller_name,
            start_days=start_days,
            converter=tz,
        )

    if view_key == "mcs":
        room_id = _coerce_int(filter_value) if filter_field == "room" else None
        caller_id = _coerce_int(filter_value) if filter_field == "caller" else None
        start_from = _coerce_datetime(filter_value) if filter_field == "start_from" else None
        start_to = _coerce_datetime(filter_value) if filter_field == "start_to" else None
        room_number = filter_value if filter_field == "room_number" else None
        caller_name = filter_value if filter_field == "caller_name" else None
        start_days = None
        if filter_field == "start_day":
            try:
                parsed_days = parse_month_day_list(filter_value)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            start_days = parsed_days or None
        return mcs_service.list_mcs(
            q=search,
            sort=normalized_sort,
            page=page,
            page_size=page_size,
            room_id=room_id,
            caller_cuer_id=caller_id,
            start_from=start_from,
            start_to=start_to,
            room_number=room_number,
            caller_name=caller_name,
            start_days=start_days,
            converter=tz,
        )

    if view_key == "profiles":
        caller_id = (
            _coerce_int(filter_value)
            if filter_field in {"caller", "caller_cuer_id"}
            else None
        )
        has_image = _coerce_bool(filter_value) if filter_field == "has_image" else None
        has_content = _coerce_bool(filter_value) if filter_field == "has_content" else None
        advertisement = (
            _coerce_bool(filter_value) if filter_field == "advertisement" else None
        )
        return profiles_service.list_profiles(
            q=search,
            sort=normalized_sort,
            page=page,
            page_size=page_size,
            caller_cuer_id=caller_id,
            has_image=has_image,
            has_content=has_content,
            advertisement=advertisement,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported view for advanced query",
    )
