# Vision Extractor

Extracción de SKUs y precios desde PDF usando **solo Vision sobre imagen completa de página**.

## Requisitos

- `OPENAI_API_KEY` configurado.
- Dependencia `pymupdf` instalada.

## Ejemplos

### Procesar una sola página (1-index)

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --start-page 71 \
  --end-page 71
```

### Procesar un rango con páginas omitidas

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --start-page 1 \
  --end-page 120 \
  --skip-pages 2,5,9
```

### Permitir consolidado parcial

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --allow-partial
```

## Salidas

- JSON por página: `output/vision/<catalog>/<cycle>/page_XXXX.json`
- Consolidado por SKU: `output/vision/<catalog>/<cycle>/by_sku.json` (solo si no hay errores o si se usa `--allow-partial`)
