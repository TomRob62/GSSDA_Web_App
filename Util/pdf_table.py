"""Convert table data into a simple PDF document."""

from __future__ import annotations

from typing import List, Sequence, Tuple

from .pdf_writer import MARGIN, PAGE_HEIGHT, render_pdf


def build_pdf_table(title: str, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> bytes:
    """Return PDF bytes containing ``rows`` rendered beneath ``title``."""

    lines = _build_table_lines(headers, rows)
    items = [(title, 16), ("", 12)] + [(line, 10) for line in lines]
    pages = _paginate(items)
    return render_pdf(pages)


def _build_table_lines(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> List[str]:
    splits = [[_split_cell(cell) for cell in row] for row in rows]
    col_widths = _column_widths(headers, splits)

    header_line = _format_row(headers, col_widths)
    separator = _separator(col_widths)
    lines = [header_line, separator]

    for row_segments in splits:
        height = max(len(parts) for parts in row_segments) if row_segments else 1
        for index in range(height):
            line_cells = [parts[index] if index < len(parts) else "" for parts in row_segments]
            lines.append(_format_row(line_cells, col_widths))
        lines.append(separator)

    if not splits:
        lines.append(separator)
    return lines


def _split_cell(value) -> List[str]:
    text = "" if value is None else str(value)
    parts = text.splitlines() or [""]
    return [part.strip() for part in parts]


def _column_widths(headers: Sequence[str], rows: Sequence[Sequence[List[str]]]) -> List[int]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, parts in enumerate(row):
            for part in parts:
                widths[index] = max(widths[index], len(part))
    return [width + 2 for width in widths]


def _format_row(cells: Sequence[str], widths: Sequence[int]) -> str:
    padded = [str(cell).ljust(widths[index]) for index, cell in enumerate(cells)]
    return " | ".join(padded)


def _separator(widths: Sequence[int]) -> str:
    return "-+-".join("-" * width for width in widths)


def _paginate(items: Sequence[Tuple[str, int]]) -> List[List[Tuple[str, int]]]:
    usable_height = PAGE_HEIGHT - (2 * MARGIN)
    pages: List[List[Tuple[str, int]]] = []
    current: List[Tuple[str, int]] = []
    used = 0
    for text, size in items:
        step = size + 4
        if current and used + step > usable_height:
            pages.append(current)
            current = []
            used = 0
        current.append((text, size))
        used += step
    if not current:
        current.append(("", 10))
    pages.append(current)
    return pages
