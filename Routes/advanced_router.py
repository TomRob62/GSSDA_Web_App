"""API routes that expose the advanced search endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from DAL import schemas
from Services import auth as auth_service
from Controllers import advanced_controller

router = APIRouter(prefix="/advanced", tags=["advanced"])


@router.get("", response_model=schemas.PaginatedResponse)
async def advanced_query(
    view: str = Query(..., description="Target resource view"),
    search: str | None = Query(None, description="Free-text search"),
    sort: str | None = Query(None, description="Sort instruction"),
    filter_field: str | None = Query(None, description="Field-specific filter key"),
    filter_value: str | None = Query(None, description="Value for the selected filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    timezone: str | None = Query(None, description="IANA timezone name for localisation"),
    user=Depends(auth_service.get_current_user),
):
    """Execute an advanced search for the requested view."""

    return advanced_controller.advanced_query_controller(
        view=view,
        search=search,
        sort=sort,
        filter_field=filter_field,
        filter_value=filter_value,
        page=page,
        page_size=page_size,
        timezone=timezone,
    )
