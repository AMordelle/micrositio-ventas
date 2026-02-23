from pathlib import Path

from pdf2image import convert_from_path, pdfinfo_from_path


def get_pdf_page_count(pdf_path: Path) -> int:
    pdf_info = pdfinfo_from_path(str(pdf_path))
    return int(pdf_info["Pages"])


def convert_pdf_to_png_pages(
    pdf_path: Path,
    output_dir: Path,
    pages: list[int],
    dpi: int = 200,
) -> list[tuple[int, Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pages:
        return []

    if any(page < 1 for page in pages):
        raise ValueError("All pages must be >= 1")

    unique_pages = sorted(set(pages))

    page_paths: list[tuple[int, Path]] = []
    for page_num in unique_pages:
        pil_pages = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
            fmt="png",
        )
        if not pil_pages:
            raise ValueError(f"Could not render page {page_num}")

        out_path = output_dir / f"page_{page_num:04d}.png"
        pil_pages[0].save(out_path, format="PNG")
        page_paths.append((page_num, out_path))

    return page_paths
