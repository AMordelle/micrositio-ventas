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

    def extract_page_json(self, image_path: Path) -> dict[str, Any]:
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

        text_output = getattr(response, "output_text", None)
        if text_output:
            return self._parse_json_output(text_output)

        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []):
                if getattr(content, "type", "") in {"output_text", "text"}:
                    return self._parse_json_output(content.text)

        raise ValueError("OpenAI response did not include JSON text output")

    @staticmethod
    def _parse_json_output(raw_text: str) -> dict[str, Any]:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI response output_text is not valid JSON") from exc
