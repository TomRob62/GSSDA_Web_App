"""
Controller functions for Caller/Cuer operations.

This module adapts the service layer outputs to Pydantic schemas and
handles conversion of comma-separated dance type strings into lists.
"""

from __future__ import annotations

from typing import List

from DAL import schemas
from Services import caller_cuers as caller_service


def _split_dance_types(dance_types: str | None) -> List[str]:
    """Utility to split a comma‑separated dance type string into a list."""
    return dance_types.split(",") if dance_types else []


def _convert_caller(caller: dict) -> schemas.CallerCuerOut:
    """Convert a raw caller dict from the service layer to a Pydantic model."""
    return schemas.CallerCuerOut(
        id=caller["id"],
        first_name=caller["first_name"],
        last_name=caller["last_name"],
        suffix=caller["suffix"],
        mc=caller["mc"],
        dance_types=caller.get("dance_types", []),
        created_at=caller["created_at"],
        updated_at=caller["updated_at"],
        version=caller.get("version", 1),
    )


def create_caller_controller(data: schemas.CallerCuerCreate) -> schemas.CallerCuerOut:
    """Create a caller/cuer and convert to response schema."""

    caller_dict = caller_service.create_caller(data)
    return _convert_caller(caller_dict)


def list_callers_controller(
    *,
    q: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 50,
    mc: bool | None = None,
    dance_type: str | None = None,
) -> schemas.PaginatedResponse:
    """Return paginated list of callers from the service layer."""
    callers, total = caller_service.list_callers(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        mc=mc,
        dance_type=dance_type,
    )
    data = [_convert_caller(c) for c in callers]
    return schemas.PaginatedResponse(
        data=data, page=page, page_size=page_size, total=total
    )


def get_caller_controller(caller_id: int) -> schemas.CallerCuerOut:
    """Return a caller/cuer by identifier."""

    caller_dict = caller_service.get_caller(caller_id)
    return _convert_caller(caller_dict)


def update_caller_controller(caller_id: int, data: schemas.CallerCuerUpdate) -> schemas.CallerCuerOut:
    """Update a caller/cuer and convert to schema."""

    caller_dict = caller_service.update_caller(caller_id, data)
    return _convert_caller(caller_dict)


def delete_caller_controller(caller_id: int, cascade: bool = False) -> None:
    """Delete a caller/cuer record."""

    caller_service.delete_caller(caller_id, cascade)


# Re-export converter for other controllers (e.g. advanced search)
convert_caller = _convert_caller