from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_skip_pages(raw_skip_pages: str | None) -> set[int]:
    if not raw_skip_pages:
        return set()

    pages: set[int] = set()
    for token in raw_skip_pages.split(","):
        cleaned = token.strip()
        if not cleaned:
            continue
        if not cleaned.isdigit():
            raise ValueError(f"Invalid skip-pages value '{cleaned}'. Expected comma-separated integers.")
        pages.add(int(cleaned))
    return pages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vision extractor phase 1 for catalog PDFs")
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
    parser.add_argument("--catalog", required=True, help="Catalog slug, e.g. natura")
    parser.add_argument("--cycle", required=True, help="Cycle id, e.g. 2026-03")
    parser.add_argument("--start-page", type=int, default=None, help="Start page (1-indexed)")
    parser.add_argument("--end-page", type=int, default=None, help="End page (1-indexed)")
    parser.add_argument("--skip-pages", default=None, help="Comma-separated page numbers to skip")
    parser.add_argument("--model", default="gpt-4.1", help="OpenAI model for Vision")
    parser.add_argument(
        "--save-images",
        action="store_true",
        help="Save rendered PNG files for debugging (default: false)",
    )
    return parser


def main() -> None:
    from pipeline.vision_extractor.render_pdf import get_pdf_page_count, render_pages, select_pages
    from pipeline.vision_extractor.utils_io import ensure_dir, save_json

    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    total_pages = get_pdf_page_count(pdf_path)
    skip_pages = parse_skip_pages(args.skip_pages)
    selected_pages = select_pages(total_pages, args.start_page, args.end_page, skip_pages)

    output_dir = Path("output") / "vision" / args.catalog / args.cycle
    images_dir = output_dir / "images"
    ensure_dir(output_dir)

    from pipeline.vision_extractor.vision_client import VisionPhase1Client

    client = VisionPhase1Client(model=args.model)

    pages_processed = 0
    pages_ok = 0
    pages_error = 0

    rendered_pages = render_pages(pdf_path=pdf_path, pages=selected_pages, zoom=2.0)
    for rendered in rendered_pages:
        pages_processed += 1
        page_number = rendered.page_number

        try:
            logging.info("page=%s render ok", page_number)

            if args.save_images:
                ensure_dir(images_dir)
                image_path = images_dir / f"page_{page_number:04d}.png"
                image_path.write_bytes(rendered.image_bytes)

            extraction = client.extract_page_with_retry(page_number=page_number, image_bytes=rendered.image_bytes, retries=1)
            logging.info("page=%s vision ok", page_number)

            json_path = output_dir / f"page_{page_number:04d}.json"
            save_json(json_path, extraction.model_dump())
            pages_ok += 1
            logging.info("page=%s saved %s", page_number, json_path)
        except Exception as exc:  # noqa: BLE001
            pages_error += 1
            logging.error("page=%s error=%s", page_number, exc)

    logging.info(
        "finished pages_processed=%s pages_ok=%s pages_error=%s",
        pages_processed,
        pages_ok,
        pages_error,
    )


if __name__ == "__main__":
    main()
