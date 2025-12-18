"""Controller layer for advanced search operations."""

from __future__ import annotations

from fastapi import HTTPException, status

from DAL import schemas
from Services import advanced as advanced_service
from Controllers.rooms_controller import convert_room
from Controllers.caller_cuers_controller import convert_caller
from Controllers.events_controller import convert_event
from Controllers.mcs_controller import convert_mc
from Controllers.profiles_controller import convert_profile
from Util.timezone_helpers import get_converter


def advanced_query_controller(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
    page: int = 1,
    page_size: int = 50,
    timezone: str | None = None,
) -> schemas.PaginatedResponse:
    """Execute an advanced query and return the results as Pydantic models."""

    try:
        tz = get_converter(timezone)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    records, total = advanced_service.query_resources(
        view=view,
        search=search,
        sort=sort,
        filter_field=filter_field,
        filter_value=filter_value,
        page=page,
        page_size=page_size,
        timezone=tz,
    )

    view_key = view.lower()
    if view_key == "rooms":
        data = [convert_room(record) for record in records]
    elif view_key == "caller_cuers":
        data = [convert_caller(record) for record in records]
    elif view_key == "events":
        data = [convert_event(record) for record in records]
    elif view_key == "mcs":
        data = [convert_mc(record) for record in records]
    elif view_key == "profiles":
        data = [convert_profile(record) for record in records]
    else:  # pragma: no cover - should be unreachable due to service validation
        data = []

    return schemas.PaginatedResponse(
        data=data,
        page=page,
        page_size=page_size,
        total=total,
    )
