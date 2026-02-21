#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from pipeline.vision_extractor.merge_by_sku import merge_pages_by_sku
from pipeline.vision_extractor.openai_client import VisionOpenAIClient
from pipeline.vision_extractor.pdf_to_images import convert_pdf_to_png_pages


VALID_CATALOGS = {"natura", "avon", "casa_estilo"}
DEFAULT_MODEL = "gpt-4.1-mini"


def _validate_page_payload(payload: dict[str, Any], page_num: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Vision output is not a JSON object")
    if "page" not in payload:
        payload["page"] = page_num
    if payload.get("page") != page_num:
        payload["page"] = page_num
    if "items" not in payload or not isinstance(payload["items"], list):
        raise ValueError("Vision output missing 'items' array")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vision-based SKU extraction from catalog PDF")
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--catalog", required=True, choices=sorted(VALID_CATALOGS))
    parser.add_argument("--cycle", required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--retry", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--start-page", type=int, default=None)
    parser.add_argument("--end-page", type=int, default=None)
    parser.add_argument("--sleep-ms", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")

    out_dir = args.out or Path("output") / "vision" / args.catalog / args.cycle
    pages_dir = out_dir / "pages"
    page_json_dir = out_dir / "page_json"
    pages_dir.mkdir(parents=True, exist_ok=True)
    page_json_dir.mkdir(parents=True, exist_ok=True)

    page_images = convert_pdf_to_png_pages(
        pdf_path=args.pdf,
        output_dir=pages_dir,
        dpi=args.dpi,
        start_page=args.start_page,
        end_page=args.end_page,
        max_pages=args.max_pages,
    )

    client = VisionOpenAIClient(model=args.model)

    parsed_pages: list[dict[str, Any]] = []
    error_pages: list[dict[str, Any]] = []

    for page_num, image_path in page_images:
        attempts = args.retry + 1
        last_error: str | None = None
        parsed: dict[str, Any] | None = None

        for _ in range(attempts):
            try:
                raw_json = client.extract_page_json(image_path)
                parsed = _validate_page_payload(raw_json, page_num)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)

        page_json_path = page_json_dir / f"page_{page_num:04d}.json"

        if parsed is None:
            error_doc = {
                "page": page_num,
                "items": [],
                "error": last_error or "Unknown extraction error",
            }
            page_json_path.write_text(json.dumps(error_doc, ensure_ascii=False, indent=2), encoding="utf-8")
            error_pages.append({"page": page_num, "error": error_doc["error"]})
        else:
            page_json_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
            parsed_pages.append(parsed)

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000)

    by_sku, unmatched_items, conflicts = merge_pages_by_sku(
        page_docs=parsed_pages,
        catalog=args.catalog,
        cycle=args.cycle,
    )

    (out_dir / "by_sku.json").write_text(json.dumps(by_sku, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "unmatched_items.json").write_text(
        json.dumps(unmatched_items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "conflicts.json").write_text(json.dumps(conflicts, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "catalog": args.catalog,
        "cycle": args.cycle,
        "pdf": str(args.pdf),
        "pages_total_rendered": len(page_images),
        "pages_ok": len(parsed_pages),
        "pages_error": len(error_pages),
        "error_pages": error_pages,
        "skus_merged": len(by_sku),
        "unmatched_items": len(unmatched_items),
        "conflicts": len(conflicts),
        "output_dir": str(out_dir),
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
