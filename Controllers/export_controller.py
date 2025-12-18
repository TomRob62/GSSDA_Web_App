"""Controller for exporting filtered views as PDF documents."""

from __future__ import annotations

from typing import Callable

from fastapi import HTTPException, status

from Services import export as export_service
from Services import export_excel as export_excel_service


def _run_export(operation: Callable[[], tuple[bytes, str]]):
    try:
        return operation()
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def export_view_controller(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
) -> tuple[bytes, str]:
    """Return PDF bytes and filename for the requested view export."""

    return _run_export(
        lambda: export_service.export_view(
            view=view,
            search=search,
            sort=sort,
            filter_field=filter_field,
            filter_value=filter_value,
        )
    )


def export_excel_view_controller(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
) -> tuple[bytes, str]:
    """Return Excel bytes and filename for the requested view export."""

    return _run_export(
        lambda: export_excel_service.export_view_excel(
            view=view,
            search=search,
            sort=sort,
            filter_field=filter_field,
            filter_value=filter_value,
        )
    )
