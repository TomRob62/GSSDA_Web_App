"""Routes exposing export functionality."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from Services import auth as auth_service
from Controllers import export_controller


router = APIRouter(prefix="/export", tags=["export"])


def _export_params(
    view: str,
    search: str | None,
    sort: str | None,
    filter_field: str | None,
    filter_value: str | None,
) -> dict[str, str | None]:
    return {
        "view": view,
        "search": search,
        "sort": sort,
        "filter_field": filter_field,
        "filter_value": filter_value,
    }


@router.get("", response_class=Response)
async def export_view(
    view: str = Query(..., description="Target resource view"),
    search: str | None = Query(None, description="Free-text search value"),
    sort: str | None = Query(None, description="Sort instruction"),
    filter_field: str | None = Query(None, description="Filter field key"),
    filter_value: str | None = Query(None, description="Filter field value"),
    user=Depends(auth_service.get_current_user),
):
    """Download a PDF export of the current filtered view."""

    pdf_bytes, filename = export_controller.export_view_controller(
        **_export_params(view, search, sort, filter_field, filter_value)
    )
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/excel", response_class=Response)
async def export_view_excel(
    view: str = Query(..., description="Target resource view"),
    search: str | None = Query(None, description="Free-text search value"),
    sort: str | None = Query(None, description="Sort instruction"),
    filter_field: str | None = Query(None, description="Filter field key"),
    filter_value: str | None = Query(None, description="Filter field value"),
    user=Depends(auth_service.get_current_user),
):
    """Download an Excel export of the current filtered view."""

    workbook_bytes, filename = export_controller.export_excel_view_controller(
        **_export_params(view, search, sort, filter_field, filter_value)
    )
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=workbook_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
