import json
from argparse import Namespace
from pathlib import Path

import pytest

from pipeline.vision_extractor import run_vision_extract


class _FakeClient:
    def __init__(self, model: str) -> None:
        self.model = model

    def extract_page_json(self, image_path: Path, page_num: int):
        return {
            "page": page_num,
            "items": [],
            "warnings": ["NON_JSON_OUTPUT_FALLBACK"],
            "_raw_output": "modelo respondió texto no json",
        }


def test_parse_page_spec_mixed_values():
    assert run_vision_extract.parse_page_spec("1,2,3,5-10") == {1, 2, 3, 5, 6, 7, 8, 9, 10}


def test_parse_page_spec_mixed_values_with_spaces():
    assert run_vision_extract.parse_page_spec(" 1, 2 , 5-6 ") == {1, 2, 5, 6}


@pytest.mark.parametrize("value", ["10-5", "0", "a"])
def test_parse_page_spec_invalid(value: str):
    with pytest.raises(ValueError):
        run_vision_extract.parse_page_spec(value)


def test_select_pages_to_process_with_skip_ranges():
    pages_selected, pages_processed = run_vision_extract.select_pages_to_process(
        total_pages=20,
        start_page=1,
        end_page=10,
        skip_pages=run_vision_extract.parse_page_spec("2,5-7"),
        max_pages=None,
    )

    assert pages_selected == [1, 3, 4, 8, 9, 10]
    assert pages_processed == [1, 3, 4, 8, 9, 10]


def test_main_counts_empty_items_page_as_ok_and_writes_raw(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "catalog.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    page_image = tmp_path / "page_0001.png"
    page_image.write_bytes(b"png")

    out_dir = tmp_path / "out"

    args = Namespace(
        pdf=pdf_path,
        catalog="natura",
        cycle="c01",
        out=out_dir,
        dpi=200,
        model="gpt-4.1-mini",
        retry=0,
        max_pages=None,
        start_page=1,
        end_page=None,
        skip_pages=None,
        sleep_ms=0,
    )

    monkeypatch.setattr(run_vision_extract, "parse_args", lambda: args)
    monkeypatch.setattr(run_vision_extract, "get_pdf_page_count", lambda _pdf: 1)
    monkeypatch.setattr(
        run_vision_extract,
        "convert_pdf_to_png_pages",
        lambda **kwargs: [(1, page_image)],
    )
    monkeypatch.setattr(run_vision_extract, "VisionOpenAIClient", _FakeClient)
    monkeypatch.setattr(run_vision_extract, "merge_pages_by_sku", lambda **kwargs: ({}, [], []))

    exit_code = run_vision_extract.main()

    assert exit_code == 0

    summary = json.loads((out_dir / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["start_page"] == 1
    assert summary["end_page"] is None
    assert summary["skip_pages_raw"] is None
    assert summary["pages_selected"] == [1]
    assert summary["pages_total_pdf"] == 1
    assert summary["pages_total_rendered"] == 1
    assert summary["pages_processed"] == 1
    assert summary["pages_ok"] == 1
    assert summary["pages_error"] == 0
    assert summary["error_pages"] == []

    page_doc = json.loads((out_dir / "page_json" / "page_0001.json").read_text(encoding="utf-8"))
    assert page_doc["items"] == []
    assert page_doc["warnings"] == ["NON_JSON_OUTPUT_FALLBACK"]
    assert "_raw_output" not in page_doc

    raw = (out_dir / "page_json" / "page_0001.raw.txt").read_text(encoding="utf-8")
    assert raw == "modelo respondió texto no json"
