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



### Extraer solo páginas candidatas de descuento

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --only-discount-pages
```

Con este flag se genera `filter_report.json` y las páginas no candidatas se guardan con `items=[]`.

### Guardar imágenes renderizadas

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --start-page 21 \
  --end-page 21 \
  --save-images
```

### Usar whitelist de SKUs válidos

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --sku-universe output/skus/all_skus_c18.json
```

### Omitir SKU index scan

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --skip-sku-index
```

### Controlar auditoría estructural

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/natura_c18.pdf \
  --catalog natura \
  --cycle c18 \
  --no-audit
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
- PNG por página (opcional con `--save-images`): `output/vision/<catalog>/<cycle>/pages/page_XXXX.png`
- Consolidado por SKU: `output/vision/<catalog>/<cycle>/by_sku.json` (solo si no hay errores o si se usa `--allow-partial`)
- Reporte de filtro (con `--only-discount-pages`): `output/vision/<catalog>/<cycle>/filter_report.json`
- Auditoría estructural Vision (default, desactivar con `--no-audit`): `output/vision/<catalog>/<cycle>/vision_audit.json`
- SKU index por página (default, desactivar con `--skip-sku-index`): `output/vision/<catalog>/<cycle>/sku_index/page_XXXX.json`
- Whitelist opcional para sku_index (`--sku-universe`): JSON con lista de SKUs válidos
