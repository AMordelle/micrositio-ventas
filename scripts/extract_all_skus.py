#!/usr/bin/env python3
# scripts/extract_all_skus.py

import re
import json
import argparse
from pathlib import Path
from typing import List, Set, Dict
import fitz  # PyMuPDF

# --------------------------------------------------------
# REGLAS DE EXTRACCIÓN
# --------------------------------------------------------

# Natura / Avon Hogar → SKUs dentro de paréntesis (3–6 dígitos)
RGX_PARENTESIS = re.compile(r"\((\d{3,6})\)")

# Avon Belleza → token numérico entero de 5–6 dígitos (NO precios)
RGX_AVON_TOKEN = re.compile(r"\b(\d{5,6})\b")


def extract_skus_parentesis(pdf_path: Path) -> List[str]:
    """Extrae SKUs entre paréntesis para Natura y Avon Hogar."""
    print(f"📄 Leyendo PDF (paréntesis): {pdf_path.name}")
    doc = fitz.open(pdf_path)
    found: Set[str] = set()

    for page in doc:
        text = page.get_text("text")
        for sku in RGX_PARENTESIS.findall(text):
            found.add(sku)

    doc.close()
    return sorted(found, key=lambda x: int(x))


def extract_skus_avon_belleza(pdf_path: Path) -> List[str]:
    """Extrae SKUs tipo Avon Belleza: 5–6 dígitos enteros, evitando precios."""
    print(f"📄 Leyendo PDF (Avon Belleza): {pdf_path.name}")
    doc = fitz.open(pdf_path)
    found: Set[str] = set()

    for page in doc:
        text = page.get_text("text")

        for m in RGX_AVON_TOKEN.finditer(text):
            sku = m.group(1)

            # Evitar precios: "$10399", "10.399", "10,399"
            start = m.start()
            left = text[max(0, start - 4):start]

            if "$" in left or "." in left or "," in left:
                continue

            found.add(sku)

    doc.close()
    return sorted(found, key=lambda x: int(x))


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------

def main(ciclo: str):
    INPUT_DIR = Path("input_pdfs")
    OUTPUT_DIR = Path("output/skus")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE = OUTPUT_DIR / f"all_skus_{ciclo}.json"

    pdfs = list(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print("❌ No hay PDFs en input_pdfs/")
        return

    print("\n=========================================")
    print("📁 PDFs que serán procesados:")
    for pdf in pdfs:
        print(f"   • {pdf.name}")
    print("=========================================\n")

    # Reporte por PDF
    stats: Dict[str, int] = {}

    all_skus: Set[str] = set()

    for pdf in pdfs:
        name = pdf.name.lower()

        if "belleza" in name:
            skus = extract_skus_avon_belleza(pdf)
        else:
            skus = extract_skus_parentesis(pdf)

        stats[pdf.name] = len(skus)
        all_skus.update(skus)

    final = sorted(all_skus, key=lambda x: int(x))

    # Guardar archivo final
    OUTPUT_FILE.write_text(
        json.dumps(final, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Resumen final
    print("\n=========================================")
    print("📊 RESUMEN DE EXTRACCIÓN POR PDF:")
    for pdf_name, count in stats.items():
        print(f"   • {pdf_name:<25} → {count:>4} SKUs")

    print("-----------------------------------------")
    print(f"✔ TOTAL SKUs ÚNICOS: {len(final)}")
    print(f"✔ Archivo generado: {OUTPUT_FILE}")
    print("=========================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", required=True, help="Ciclo actual (ej. 202517)")
    args = parser.parse_args()
    main(args.cycle)
