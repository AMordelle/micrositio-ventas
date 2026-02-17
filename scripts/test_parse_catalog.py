#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


import json
from pathlib import Path

from pipeline.extract.extract_pipeline import extract_pdf
from pipeline.parse.page_router import PageRouter

CLASSIFICATION_DIR = Path("output/page_classification")
INPUT_DIR = Path("input_pdfs")
OUTPUT_DIR = Path("output/parsed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_classification(pdf_name):
    """Carga el archivo *_classification.json generado por el classifier."""
    file = CLASSIFICATION_DIR / f"{pdf_name}_classification.json"
    if not file.exists():
        raise FileNotFoundError(f"No existe clasificación: {file}")
    return json.loads(file.read_text(encoding="utf-8"))

def test_parse(pdf_path: Path):
    print(f"\n=== Procesando catálogo: {pdf_path.name} ===\n")

    # Cargar clasificación de páginas
    classification = load_classification(pdf_path.stem)

    # Extraer texto original
    pages_text = extract_pdf(str(pdf_path))

    router = PageRouter()
    productos = []

    total_pages = classification["total_pages"]
    for page_number in range(1, total_pages+1):

        meta = classification["pages"].get(str(page_number))
        if not meta:
            continue

        detected_type = meta["detected_type"]

        # Evitar procesar páginas sin contenido útil
        if detected_type in ("UNKNOWN", "PROMO_BANNER"):
            continue

        text = pages_text.get(page_number, "")
        page_meta = {
            "page": page_number,
            "detected_type": detected_type
        }

        salida = router.parse_page(text, page_meta, pdf_path.name)

        if salida:
            productos.extend(salida)

    # Exportar productos encontrados
    out_path = OUTPUT_DIR / f"{pdf_path.stem}_parsed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(productos, f, indent=2, ensure_ascii=False)

    print(f"\n✔ Archivo generado: {out_path}\n")
    print(f"✔ Total de productos extraídos: {len(productos)}\n")

def main():
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print("No hay PDFs en input_pdfs/")
        return

    for pdf in pdfs:
        test_parse(pdf)

if __name__ == "__main__":
    main()
