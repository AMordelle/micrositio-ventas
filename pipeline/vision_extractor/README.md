# Vision Extractor (FASE 1)

Este módulo implementa una primera versión de extracción visual de catálogos PDF usando OpenAI Responses API (Vision), procesando páginas completas como imagen.

## Qué hace esta fase

- Convierte páginas PDF a PNG con PyMuPDF (render 2x).
- Permite seleccionar páginas con:
  - `--start-page`
  - `--end-page`
  - `--skip-pages`
- Envía cada página completa a Vision (`detail="high"`).
- Valida salida con esquema Pydantic de FASE 1.
- Reintenta 1 vez si la respuesta no es JSON válido o no cumple esquema.
- Guarda un JSON por página en:
  - `output/vision/<catalog>/<cycle>/page_XXXX.json`

## Estructura de salida FASE 1

```json
{
  "page": 14,
  "blocks": [
    {
      "title": "string|null",
      "description": "string|null",
      "is_kit": false,
      "kit_includes": [],
      "prices": {
        "currency": "MXN",
        "regular": null,
        "sale": null
      },
      "discount_text": "string|null"
    }
  ]
}
```

## Reglas importantes

- No calcula porcentajes.
- No infiere descuentos.
- `discount_text` se conserva textual tal como aparezca.
- Si un dato no aparece, se guarda `null` (o lista vacía en `kit_includes`).
- No genera `by_sku.json` en esta fase.

## Uso

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/Natura202603.pdf \
  --catalog natura \
  --cycle 2026-03 \
  --start-page 14 \
  --end-page 20 \
  --skip-pages 17,18
```

En el ejemplo se procesan las páginas: `14,15,16,19,20`.

## Variables de entorno

- `OPENAI_API_KEY` (obligatoria)

## Opción de debug

- `--save-images`: guarda PNG renderizados en `output/vision/<catalog>/<cycle>/images`.
