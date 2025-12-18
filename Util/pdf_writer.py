"""Low-level helpers for building tiny PDF documents."""

from __future__ import annotations

from typing import List, Sequence, Tuple


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN = 40


def render_pdf(pages: Sequence[Sequence[Tuple[str, int]]]) -> bytes:
    """Render ``pages`` (each a list of ``(text, font_size)`` tuples) to PDF bytes."""

    objects: List[str | None] = [None]
    font_id = _add_object(objects, "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_refs: List[Tuple[int, int]] = []
    for page in pages:
        stream = _build_content_stream(page)
        content = f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream"
        content_id = _add_object(objects, content)
        page_id = _add_object(objects, None)
        page_refs.append((page_id, content_id))

    pages_id = _add_object(objects, None)
    catalog_id = _add_object(objects, None)

    kids = " ".join(f"{page_id} 0 R" for page_id, _ in page_refs)
    objects[pages_id] = f"<< /Type /Pages /Count {len(page_refs)} /Kids [{kids}] >>"
    for page_id, content_id in page_refs:
        objects[page_id] = (
            "<< /Type /Page /Parent {parent} 0 R /MediaBox [0 0 {width} {height}] "
            "/Contents {content} 0 R /Resources << /Font << /F1 {font} 0 R >> >> >>"
        ).format(
            parent=pages_id,
            width=PAGE_WIDTH,
            height=PAGE_HEIGHT,
            content=content_id,
            font=font_id,
        )
    objects[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>"

    return _build_pdf_bytes(objects, catalog_id)


def _add_object(objects: List[str | None], content: str | None) -> int:
    objects.append(content)
    return len(objects) - 1


def _build_content_stream(items: Sequence[Tuple[str, int]]) -> str:
    y = PAGE_HEIGHT - MARGIN
    commands: List[str] = []
    for text, size in items:
        y -= size
        commands.append(
            "BT /F1 {size} Tf {x} {y} Td ({text}) Tj ET".format(
                size=size,
                x=MARGIN,
                y=max(y, MARGIN),
                text=_escape(text),
            )
        )
        y -= 4
    return "\n".join(commands)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf_bytes(objects: Sequence[str | None], catalog_id: int) -> bytes:
    output = bytearray()
    output.extend(b"%PDF-1.4\n")

    offsets: List[int] = []
    for index, content in enumerate(objects[1:], start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("latin-1"))
        body = (content or "").encode("latin-1")
        output.extend(body)
        if not body.endswith(b"\n"):
            output.extend(b"\n")
        output.extend(b"endobj\n")

    xref_position = len(output)
    total = len(objects)
    output.extend(f"xref\n0 {total}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    trailer = f"trailer\n<< /Size {total} /Root {catalog_id} 0 R >>\nstartxref\n{xref_position}\n%%EOF"
    output.extend(trailer.encode("latin-1"))
    return bytes(output)
