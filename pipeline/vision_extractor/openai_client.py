import base64
import json
from pathlib import Path
from typing import Any

from .prompts import VISION_PROMPT


class VisionOpenAIClient:
    """Small wrapper around OpenAI Responses API for page-level vision extraction."""

    def __init__(self, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model

    def extract_page_json(self, image_path: Path, page_num: int) -> dict[str, Any]:
        image_base64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        response = self._create_response(image_base64)
        raw_text = self._extract_raw_text(response)

        if raw_text is None:
            return self._non_json_fallback(page_num=page_num, raw_text="")

        return self._parse_json_output(raw_text=raw_text, page_num=page_num)

    def _create_response(self, image_base64: str):
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": VISION_PROMPT},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{image_base64}",
                        },
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            return self.client.responses.create(**payload)
        except Exception as exc:  # noqa: BLE001
            if "response_format" not in str(exc):
                raise
            payload.pop("response_format", None)
            return self.client.responses.create(**payload)

    @staticmethod
    def _extract_raw_text(response: Any) -> str | None:
        text_output = getattr(response, "output_text", None)
        if text_output:
            return text_output

        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []):
                if getattr(content, "type", "") in {"output_text", "text"}:
                    return content.text

        return None

    def _parse_json_output(self, raw_text: str, page_num: int) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and start < end:
            candidate = raw_text[start : end + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        return self._non_json_fallback(page_num=page_num, raw_text=raw_text)

    @staticmethod
    def _non_json_fallback(page_num: int, raw_text: str) -> dict[str, Any]:
        return {
            "page": page_num,
            "items": [],
            "warnings": ["NON_JSON_OUTPUT_FALLBACK"],
            "_raw_output": raw_text,
        }
