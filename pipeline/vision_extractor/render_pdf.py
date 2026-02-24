from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class RenderedPage:
    page_number: int
    image_bytes: bytes


def get_pdf_page_count(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def select_pages(
    total_pages: int,
    start_page: int | None,
    end_page: int | None,
    skip_pages: set[int],
) -> list[int]:
    if total_pages <= 0:
        return []

    start = 1 if start_page is None else start_page
    end = total_pages if end_page is None else end_page

    if start > end:
        raise ValueError(f"Invalid page range: start-page ({start}) must be <= end-page ({end}).")
    if start < 1 or start > total_pages:
        raise ValueError(f"start-page ({start}) must be between 1 and {total_pages}.")
    if end < 1 or end > total_pages:
        raise ValueError(f"end-page ({end}) must be between 1 and {total_pages}.")

    out_of_bounds_skips = sorted(page for page in skip_pages if page < 1 or page > total_pages)
    if out_of_bounds_skips:
        bad = ", ".join(str(p) for p in out_of_bounds_skips)
        raise ValueError(f"skip-pages contains pages outside PDF range 1-{total_pages}: {bad}")

    selected = [page for page in range(start, end + 1) if page not in skip_pages]
    if not selected:
        raise ValueError("No pages selected after applying range and skip-pages filters.")
    return selected


def render_pages(pdf_path: Path, pages: list[int], zoom: float = 2.0) -> list[RenderedPage]:
    matrix = fitz.Matrix(zoom, zoom)
    rendered: list[RenderedPage] = []

    with fitz.open(pdf_path) as doc:
        for page_number in pages:
            page = doc.load_page(page_number - 1)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            rendered.append(RenderedPage(page_number=page_number, image_bytes=pix.tobytes("png")))

    return rendered
