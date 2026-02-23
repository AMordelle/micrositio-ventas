from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from pipeline.vision_extractor.schemas_phase1 import PageExtraction
from pipeline.vision_extractor.utils_io import png_to_data_url

PHASE1_PROMPT = """
Eres un extractor visual de catálogos. Analiza TODA la imagen de una página y responde SOLO JSON válido.

Debes devolver este schema FINAL exacto por página:
{
  "page": <int>,
  "items": [
    {
      "sku": "<string>",
      "title": "<string|null>",
      "variant": "<string|null>",
      "size": "<string|null>",
      "prices": { "currency": "MXN", "regular": <number|null>, "sale": <number|null> },
      "discount_badge": { "text": "<string>", "percent": <int|null>, "kind": "exact|more_than|up_to" } | null,
      "points": <int|null>
    }
  ]
}

Reglas NO negociables:
- NO calcular porcentajes desde precios.
- NO inferir descuentos no visibles.
- NO inventar valores.
- NO mezclar información entre bloques distintos.
- Si no es visible: null.

Regla de segmentación (muy importante):
- Un bloque de producto puede tener SUB-BLOQUES internos con listas de tonos/variantes.
- Cada sub-bloque tiene su propio contexto de promo/precio para sus SKUs.
- Si hay dos listas de tonos del mismo producto:
  - lista con badge + precio promo => SOLO esos SKUs con sale y discount_badge.
  - lista sin badge y sin promo => esos SKUs con sale=null y discount_badge=null.
- PROHIBIDO propagar promo/badge entre sub-bloques.

Regla de expansión por SKU:
- Si un sub-bloque muestra SKUs visibles, generar 1 item por SKU.
- sku debe ser EXACTAMENTE el número visible (ej. "(127766)" => "127766").
- variant debe usar el tono/código visible (ej. "21C").
- Si un producto/variante no tiene SKU visible, NO crear item.

Regla de "Repuesto":
- Si está marcado como "Repuesto" y no tiene badge propio:
  - discount_badge=null
  - prices.sale=null
  - prices.regular=precio visible
- Solo heredar promo si está explícitamente dentro del mismo sub-bloque con badge.

Discount badge:
- text: EXACTO tal como aparece.
- kind/percent extraídos solo del texto del badge:
  - "35% de descuento" => kind="exact", percent=35
  - "Más del 45%" => kind="more_than", percent=45
  - "Hasta 30%" => kind="up_to", percent=30
- Si no hay número claro => percent=null; kind según palabras ("Más del"/"Hasta"/default "exact").

Tamaño y puntos:
- size si aparece, por ejemplo "20 g" o "10 g".
- points si aparece, por ejemplo "34 pts" => points=34.

Importante:
- Evita duplicados inconsistentes de un mismo SKU.
- Responde SOLO JSON, sin markdown.
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

    @staticmethod
    def _extract_json(raw: str) -> Any:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
            if match:
                cleaned = match.group(1)
        return json.loads(cleaned)

    def extract_page_with_retry(self, page_number: int, image_bytes: bytes, retries: int = 1) -> PageExtraction:
        attempts = retries + 1
        last_error: Exception | None = None

        for _ in range(attempts):
            try:
                raw = self._invoke(page_number=page_number, image_bytes=image_bytes)
                payload = self._extract_json(raw)
                validated = PageExtraction.model_validate(payload)
                if validated.page != page_number:
                    validated.page = page_number
                return validated
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc

        raise RuntimeError(f"Vision output invalid for page {page_number}: {last_error}")
