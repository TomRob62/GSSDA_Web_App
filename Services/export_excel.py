"""Service orchestrating export of filtered views into Excel workbooks."""

from __future__ import annotations

import datetime as _dt

from Services import export_data
from Util.excel_writer import build_workbook_bytes


def export_view_excel(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
) -> tuple[bytes, str]:
    """Return workbook bytes and filename for the requested export."""

    title, headers, rows = export_data.collect_table(
        view=view,
        search=search,
        sort=sort,
        filter_field=filter_field,
        filter_value=filter_value,
    )
    workbook_bytes = build_workbook_bytes(title, headers, rows)
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_view = view.lower().replace("/", "-") or "export"
    filename = f"{safe_view}_{timestamp}.xlsx"
    return workbook_bytes, filename


__all__ = ["export_view_excel"]

