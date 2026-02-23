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
        self.last_raw_output: str | None = None

    def extract_page_json(self, image_path: Path, page_num: int) -> dict[str, Any]:
        self.last_raw_output = None
        image_base64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        response = self.client.responses.create(
            model=self.model,
            input=[
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
        )

        raw_text = self._extract_raw_text(response)
        if raw_text is None:
            self.last_raw_output = ""
            return {"page": page_num, "items": [], "warnings": ["NON_JSON_OUTPUT"]}

        parsed = self._parse_json_output(raw_text)
        if parsed is None:
            self.last_raw_output = raw_text
            return {"page": page_num, "items": [], "warnings": ["NON_JSON_OUTPUT"]}

        return parsed

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

    @staticmethod
    def _parse_json_output(raw_text: str) -> dict[str, Any] | None:
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
                return None

        return None
