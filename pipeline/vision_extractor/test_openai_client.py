from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.vision_extractor.openai_client import VisionOpenAIClient


class _FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text='{"ok": true}')


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponses()


def _build_client() -> tuple[VisionOpenAIClient, _FakeClient]:
    client = VisionOpenAIClient.__new__(VisionOpenAIClient)
    client.model = "gpt-test"
    fake = _FakeClient()
    client.client = fake
    return client, fake


def test_extract_page_json_sends_image_url_not_image_base64(tmp_path: Path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake-image")

    client, fake = _build_client()
    parsed = client.extract_page_json(image_path)

    assert parsed == {"ok": True}
    content = fake.responses.kwargs["input"][0]["content"]
    image_part = content[1]
    assert image_part["type"] == "input_image"
    assert "image_url" in image_part
    assert image_part["image_url"].startswith("data:image/png;base64,")
    assert "image_base64" not in image_part


def test_extract_page_json_raises_on_invalid_json(tmp_path: Path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake-image")

    client, fake = _build_client()
    fake.responses.create = lambda **kwargs: SimpleNamespace(output_text="not-json")

    with pytest.raises(ValueError, match="not valid JSON"):
        client.extract_page_json(image_path)
