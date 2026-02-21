from pathlib import Path

from pdf2image import convert_from_path, pdfinfo_from_path


def convert_pdf_to_png_pages(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 200,
    start_page: int | None = None,
    end_page: int | None = None,
    max_pages: int | None = None,
) -> list[tuple[int, Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_info = pdfinfo_from_path(str(pdf_path))
    total_pages = int(pdf_info["Pages"])

    first_page = start_page or 1
    last_page = end_page or total_pages

    if first_page < 1:
        raise ValueError("start_page must be >= 1")
    if last_page < first_page:
        raise ValueError("end_page must be >= start_page")

    if max_pages is not None:
        last_page = min(last_page, first_page + max_pages - 1)

    pil_pages = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
        fmt="png",
    )

    page_paths: list[tuple[int, Path]] = []
    for idx, page_img in enumerate(pil_pages, start=first_page):
        out_path = output_dir / f"page_{idx:04d}.png"
        page_img.save(out_path, format="PNG")
        page_paths.append((idx, out_path))

    return page_paths
