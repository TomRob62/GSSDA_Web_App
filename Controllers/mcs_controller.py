"""Controller helpers for MC routes."""

from __future__ import annotations

import datetime

from fastapi import HTTPException, status

from DAL import schemas
from Services import mcs as mc_service
from Util.timezone_helpers import TimeZoneConverter, get_converter, parse_datetime


def _convert_mc(mc: dict) -> schemas.MCOut:
    """Convert a raw MC dict to a Pydantic model."""

    return schemas.MCOut(
        id=mc["id"],
        room_id=mc["room_id"],
        caller_cuer_id=mc["caller_cuer_id"],
        start=mc["start"],
        end=mc["end"],
        created_at=mc["created_at"],
        updated_at=mc["updated_at"],
        version=mc.get("version", 1),
    )


def _resolve_timezone(value: str | None) -> TimeZoneConverter:
    """Resolve ``value`` into a converter returning HTTP 422 for invalid zones."""

    try:
        return get_converter(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _parse_optional_datetime(value: str | None, *, converter: TimeZoneConverter) -> datetime.datetime | None:
    """Parse ``value`` as an aware datetime for MC filters."""

    if not value:
        return None
    try:
        return parse_datetime(value, timezone=converter)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid datetime format") from exc


def create_mc_controller(
    data: schemas.MCCreate, *, timezone: str | None = None
) -> schemas.MCOut:
    """Create an MC record and convert it to a response schema."""

    tz = _resolve_timezone(timezone)
    mc_dict = mc_service.create_mc(data, converter=tz)
    return _convert_mc(mc_dict)


def list_mcs_controller(
    *,
    q: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 50,
    room_id: int | None = None,
    caller_cuer_id: int | None = None,
    start_from: str | None = None,
    start_to: str | None = None,
    timezone: str | None = None,
) -> schemas.PaginatedResponse:
    """Return a paginated list of MCs."""

    tz = _resolve_timezone(timezone)
    try:
        sf = _parse_optional_datetime(start_from, converter=tz)
        st = _parse_optional_datetime(start_to, converter=tz)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    mcs, total = mc_service.list_mcs(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        room_id=room_id,
        caller_cuer_id=caller_cuer_id,
        start_from=sf,
        start_to=st,
        converter=tz,
    )
    data = [_convert_mc(mc) for mc in mcs]
    return schemas.PaginatedResponse(
        data=data, page=page, page_size=page_size, total=total
    )


def get_mc_controller(mc_id: int, *, timezone: str | None = None) -> schemas.MCOut:
    """Retrieve a single MC by identifier."""

    tz = _resolve_timezone(timezone)
    mc_dict = mc_service.get_mc(mc_id, converter=tz)
    return _convert_mc(mc_dict)


def update_mc_controller(
    mc_id: int,
    data: schemas.MCUpdate,
    *,
    timezone: str | None = None,
) -> schemas.MCOut:
    """Update an MC record and convert to schema."""

    tz = get_converter(timezone)
    mc_dict = mc_service.update_mc(mc_id, data, converter=tz)
    return _convert_mc(mc_dict)


def delete_mc_controller(mc_id: int) -> None:
    """Remove an MC record."""

    mc_service.delete_mc(mc_id)


# Re-export converter for other controllers
convert_mc = _convert_mc
