"""Service orchestrating export of filtered views into PDF documents."""

from __future__ import annotations

import datetime as _dt
from typing import Tuple

from Util.pdf_table import build_pdf_table
from Services import export_data


def export_view(
    *,
    view: str,
    search: str | None = None,
    sort: str | None = None,
    filter_field: str | None = None,
    filter_value: str | None = None,
) -> Tuple[bytes, str]:
    """Return ``(pdf_bytes, filename)`` for the requested export."""

    title, headers, rows = export_data.collect_table(
        view=view,
        search=search,
        sort=sort,
        filter_field=filter_field,
        filter_value=filter_value,
    )
    pdf_bytes = build_pdf_table(title, headers, rows)
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_view = view.lower().replace("/", "-") or "export"
    filename = f"{safe_view}_{timestamp}.pdf"
    return pdf_bytes, filename
