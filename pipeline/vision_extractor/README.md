# Vision Extractor (PDF catálogo -> JSON por SKU)

## Requisitos

1. Python 3.10+
2. Dependencias Python:

```bash
pip install -r requirements.txt
```

3. Variable de entorno para OpenAI:

```bash
export OPENAI_API_KEY="tu_api_key"
```

4. **Poppler** (requerido por `pdf2image`)
- **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
- **MacOS (Homebrew)**: `brew install poppler`
- **Windows**: instalar Poppler para Windows y agregar `bin/` al `PATH`.

## Ejecución

Desde la raíz del repo:

### 1 página (usando `--max-pages 1`)

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/Natura202603.pdf \
  --catalog natura \
  --cycle 2026-03 \
  --max-pages 1
```

### Rango de páginas

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/CasaEstilo202603.pdf \
  --catalog casa_estilo \
  --cycle 2026-03 \
  --start-page 10 \
  --end-page 20
```

### Catálogo completo

```bash
python pipeline/vision_extractor/run_vision_extract.py \
  --pdf input_pdfs/Avon202603.pdf \
  --catalog avon \
  --cycle 2026-03
```

## Flags

Obligatorios:
- `--pdf <path>`
- `--catalog <natura|avon|casa_estilo>`
- `--cycle <string>`

Opcionales:
- `--out output/vision/<catalog>/<cycle>` (default)
- `--dpi 200`
- `--model gpt-4.1-mini`
- `--retry 1`
- `--max-pages N`
- `--start-page N`
- `--end-page N`
- `--sleep-ms 0`

## Outputs

Se generan en:

`output/vision/<catalog>/<cycle>/`

- `pages/page_0001.png` ...
- `page_json/page_0001.json` ...
- `by_sku.json`
- `unmatched_items.json`
- `conflicts.json`
- `run_summary.json`
