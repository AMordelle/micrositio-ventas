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

Reglas CRÍTICAS para Repuesto:
- Si hay una sección explícitamente rotulada como “Repuesto”, los SKUs de Repuesto SOLO pueden provenir de esa sección.
- Está PROHIBIDO copiar o reutilizar SKUs del producto principal (no Repuesto) para construir items de Repuesto.
- Está PROHIBIDO inventar SKUs. Si un SKU no es legible con certeza, NO generes ese item.
- Si la sección Repuesto lista tonos/códigos (ej. 12N, 19N…), variant debe ser ese código; si no se ve, variant=null.
- Repuesto solo hereda promoción si el badge de descuento está visible en el MISMO sub-bloque visual del repuesto; si no, discount_badge=null y sale=null.

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

RETRY_REPUESTO_SKU_MIX = (
    "Corrige: la sección Repuesto no puede usar SKUs del producto principal. "
    "Extrae SOLO los SKUs impresos en Repuesto. No inventes SKUs. Devuelve JSON válido."
)

RETRY_REPUESTO_VARIANT = (
    "Corrige: en Repuesto hay SKUs con variant=null. Si el sub-bloque de Repuesto muestra "
    "lista de tonos/códigos, llena variant con ese código explícito; si no es visible, deja null. "
    "No inventes SKUs y devuelve JSON válido."
)


class VisionPhase1Client:
    def __init__(self, model: str = "gpt-4.1", timeout: float = 90.0) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to run Vision extraction.")
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model

    def _invoke(self, page_number: int, image_bytes: bytes, correction: str | None = None) -> str:
        image_data_url = png_to_data_url(image_bytes)
        content: list[dict[str, str]] = [
            {"type": "input_text", "text": PHASE1_PROMPT},
            {"type": "input_text", "text": f"El número de página es {page_number}."},
        ]
        if correction:
            content.append({"type": "input_text", "text": correction})
        content.append({"type": "input_image", "image_url": image_data_url, "detail": "high"})

        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": content}],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "page_extraction",
                    "schema": PageExtraction.model_json_schema(),
                    "strict": True,
                }
            },
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

    @staticmethod
    def _is_repuesto(title: str | None) -> bool:
        return bool(title and "repuesto" in title.casefold())

    def _repuesto_guardrail_message_from_payload(self, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        items = payload.get("items")
        if not isinstance(items, list):
            return None

        non_repuesto_skus: set[str] = set()
        repuesto_entries: list[dict[str, Any]] = []

        for entry in items:
            if not isinstance(entry, dict):
                continue
            sku = entry.get("sku")
            title = entry.get("title")
            if not isinstance(sku, str):
                continue
            if self._is_repuesto(title if isinstance(title, str) else None):
                repuesto_entries.append(entry)
            else:
                non_repuesto_skus.add(sku)

        if any(isinstance(entry.get("sku"), str) and entry["sku"] in non_repuesto_skus for entry in repuesto_entries):
            return RETRY_REPUESTO_SKU_MIX

        repuesto_null_variant = [entry for entry in repuesto_entries if entry.get("variant") is None]
        if len(repuesto_entries) >= 2 and repuesto_null_variant:
            return RETRY_REPUESTO_VARIANT

        return None

    def _repuesto_guardrail_message(self, parsed: PageExtraction) -> str | None:
        non_repuesto_skus = {item.sku for item in parsed.items if not self._is_repuesto(item.title)}
        repuesto_items = [item for item in parsed.items if self._is_repuesto(item.title)]

        if any(item.sku in non_repuesto_skus for item in repuesto_items):
            return RETRY_REPUESTO_SKU_MIX

        repuesto_with_null_variant = [item for item in repuesto_items if item.variant is None]
        if len(repuesto_items) >= 2 and repuesto_with_null_variant:
            return RETRY_REPUESTO_VARIANT

        return None

    def extract_page_with_retry(self, page_number: int, image_bytes: bytes, retries: int = 1) -> PageExtraction:
        attempts = retries + 1
        last_error: Exception | None = None
        correction: str | None = None

        for attempt in range(attempts):
            try:
                raw = self._invoke(page_number=page_number, image_bytes=image_bytes, correction=correction)
                payload = self._extract_json(raw)
                payload_guardrail = self._repuesto_guardrail_message_from_payload(payload)
                if payload_guardrail and attempt < attempts - 1:
                    correction = payload_guardrail
                    continue

                validated = PageExtraction.model_validate(payload)
                if validated.page != page_number:
                    validated.page = page_number

                repuesto_message = self._repuesto_guardrail_message(validated)
                if repuesto_message and attempt < attempts - 1:
                    correction = repuesto_message
                    continue
                if repuesto_message:
                    raise ValueError(repuesto_message)
                return validated
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc

        raise RuntimeError(f"Vision output invalid for page {page_number}: {last_error}")
