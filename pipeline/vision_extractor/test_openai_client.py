from pathlib import Path
from types import SimpleNamespace

from pipeline.vision_extractor.openai_client import VisionOpenAIClient


class _FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None
        self.response = SimpleNamespace(output_text='{"ok": true}')

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


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
    parsed = client.extract_page_json(image_path=image_path, page_num=1)

    assert parsed == {"ok": True}
    content = fake.responses.kwargs["input"][0]["content"]
    image_part = content[1]
    assert image_part["type"] == "input_image"
    assert "image_url" in image_part
    assert image_part["image_url"].startswith("data:image/png;base64,")
    assert "image_base64" not in image_part
    assert fake.responses.kwargs["response_format"] == {"type": "json_object"}


def test_extract_page_json_parses_json_substring(tmp_path: Path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake-image")

    client, fake = _build_client()
    fake.responses.response = SimpleNamespace(output_text='texto previo {"page": 1, "items": []} texto final')

    parsed = client.extract_page_json(image_path=image_path, page_num=1)

    assert parsed == {"page": 1, "items": []}


def test_extract_page_json_returns_fallback_on_non_json(tmp_path: Path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake-image")

    client, fake = _build_client()
    fake.responses.response = SimpleNamespace(output_text="not-json")

    parsed = client.extract_page_json(image_path=image_path, page_num=7)

    assert parsed["page"] == 7
    assert parsed["items"] == []
    assert parsed["warnings"] == ["NON_JSON_OUTPUT_FALLBACK"]
    assert parsed["_raw_output"] == "not-json"
