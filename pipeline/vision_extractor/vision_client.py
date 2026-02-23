from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from pipeline.vision_extractor.schemas_phase1 import PageExtraction
from pipeline.vision_extractor.utils_io import png_to_data_url

PHASE1_PROMPT = """
Eres un extractor visual de catálogos. Analiza TODA la imagen de una página y responde SOLO JSON válido.

Objetivo:
- Detecta bloques visuales independientes de productos o kits.
- NO mezcles información entre bloques distintos.
- Si hay promo global con variantes, NO expandas variantes en esta fase.

Para cada bloque extrae:
- title (nombre breve visible del producto, o null)
- description (descripción visible, o null)
- is_kit (true solo si explícitamente parece kit/paquete/conjunto)
- kit_includes (lista textual de lo que incluye solo si se ve explícitamente, si no lista vacía)
- prices.currency siempre "MXN"
- prices.regular (número o null)
- prices.sale (número o null)
- discount_text (texto EXACTO tal como aparece, por ejemplo "35% de descuento", "Más del 45%", "Hasta 30%"; si no aparece, null)

Reglas críticas:
- NO calcules porcentajes.
- NO infieras descuentos.
- Si un dato no aparece, usa null (o lista vacía para kit_includes).
- Mantén discount_text exactamente como aparece en la página.

Responde este formato exacto:
{
  "page": <int>,
  "blocks": [
    {
      "title": "<string|null>",
      "description": "<string|null>",
      "is_kit": <bool>,
      "kit_includes": ["<string>", ...],
      "prices": {
        "currency": "MXN",
        "regular": <number|null>,
        "sale": <number|null>
      },
      "discount_text": "<string|null>"
    }
  ]
}
""".strip()


class VisionPhase1Client:
    def __init__(self, model: str = "gpt-4.1", timeout: float = 90.0) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to run Vision extraction.")
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model

    def _invoke(self, page_number: int, image_bytes: bytes) -> str:
        image_data_url = png_to_data_url(image_bytes)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": PHASE1_PROMPT},
                        {"type": "input_text", "text": f"El número de página es {page_number}."},
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
        )

        text = getattr(response, "output_text", None)
        if text:
            return text

        return json.dumps(response.model_dump())

    def extract_page_with_retry(self, page_number: int, image_bytes: bytes, retries: int = 1) -> PageExtraction:
        attempts = retries + 1
        last_error: Exception | None = None

        for _ in range(attempts):
            try:
                raw = self._invoke(page_number=page_number, image_bytes=image_bytes)
                payload: Any = json.loads(raw)
                validated = PageExtraction.model_validate(payload)
                if validated.page != page_number:
                    validated.page = page_number
                return validated
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc

        raise RuntimeError(f"Vision output invalid for page {page_number}: {last_error}")
