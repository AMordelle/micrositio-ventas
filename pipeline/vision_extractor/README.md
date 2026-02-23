# Vision Extractor (FASE actual)

Este módulo extrae información por página desde PDF usando OpenAI Responses API (Vision), procesando cada página completa como imagen.

## Qué hace

- Convierte páginas PDF a PNG con PyMuPDF (render 2x).
- Permite seleccionar páginas con:
  - `--start-page`
  - `--end-page`
  - `--skip-pages`
- Envía cada página completa a Vision (`detail="high"`).
- Valida salida con esquema Pydantic final por página.
- Reintenta 1 vez si la respuesta no es JSON válido o no cumple esquema.
- Guarda un JSON por página en:
  - `output/vision/<catalog>/<cycle>/page_XXXX.json`

## Estructura de salida por página

```json
{
  "page": 71,
  "items": [
    {
      "sku": "127766",
      "title": "Base matte powder multifuncional",
      "variant": "21C",
      "size": "20 g",
      "prices": {
        "currency": "MXN",
        "regular": 549,
        "sale": 356.85
      },
      "discount_badge": {
        "text": "35% de descuento",
        "percent": 35,
        "kind": "exact"
      },
      "points": 34
    }
  ]
}
```

## Reglas importantes

- No calcula porcentajes usando precios.
- No infiere descuentos no visibles.
- No inventa valores.
- Si no hay SKU visible, no se crea item.
- No mezclar información entre bloques distintos.
- Segmentación por sub-bloques: promo y precio solo aplican a SKUs del sub-bloque donde son visibles.
- No propagar promo entre listas de tonos separadas.
- Evita duplicados inconsistentes por SKU en la misma página.

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
