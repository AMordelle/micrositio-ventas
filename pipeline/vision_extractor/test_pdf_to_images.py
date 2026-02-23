from pathlib import Path

from pipeline.vision_extractor import pdf_to_images


class _FakeImage:
    def __init__(self) -> None:
        self.saved = []

    def save(self, path: Path, format: str) -> None:  # noqa: A002
        self.saved.append((str(path), format))


def test_get_pdf_page_count(monkeypatch, tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"pdf")

    monkeypatch.setattr(pdf_to_images, "pdfinfo_from_path", lambda _: {"Pages": "12"})

    assert pdf_to_images.get_pdf_page_count(pdf) == 12


def test_convert_pdf_to_png_pages_renders_selected_pages(monkeypatch, tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"pdf")
    out = tmp_path / "out"

    calls = []

    def _fake_convert(path: str, dpi: int, first_page: int, last_page: int, fmt: str):
        calls.append((path, dpi, first_page, last_page, fmt))
        return [_FakeImage()]

    monkeypatch.setattr(pdf_to_images, "convert_from_path", _fake_convert)

    rendered = pdf_to_images.convert_pdf_to_png_pages(
        pdf_path=pdf,
        output_dir=out,
        pages=[3, 1, 3, 10],
        dpi=150,
    )

    assert rendered == [
        (1, out / "page_0001.png"),
        (3, out / "page_0003.png"),
        (10, out / "page_0010.png"),
    ]
    assert calls == [
        (str(pdf), 150, 1, 1, "png"),
        (str(pdf), 150, 3, 3, "png"),
        (str(pdf), 150, 10, 10, "png"),
    ]
