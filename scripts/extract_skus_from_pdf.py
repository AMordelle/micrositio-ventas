#!/usr/bin/env python3
"""
Extractor robusto de SKUs desde catálogos PDF.

Función:
    - Detecta si el PDF tiene texto o es imagen.
    - Extrae el texto con PyMuPDF o OCR.
    - Limpia contenido.
    - Extrae SKUs usando regex inteligentes.
    - Elimina SKUs falsos, repetidos o incompletos.
    - Guarda lista final en TXT.

Requisitos:
    pip install pymupdf
    pip install pytesseract pillow      (solo si quieres OCR)
"""

import re
from pathlib import Path
from typing import List, Set

import fitz  # PyMuPDF

# Opcional para OCR (solo si lo necesitas)
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except:
    OCR_AVAILABLE = False


# -------------------------------
# CONFIG
# -------------------------------
INPUT_PDF_DIR = Path("input_pdfs")
OUTPUT_DIR = Path("output/skus")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------
# UTILIDADES
# -------------------------------

def is_text_pdf(pdf_path: Path) -> bool:
    """Detecta si el PDF tiene texto seleccionable."""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text().strip()
            if len(text) > 20:
                return True
    return False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrae texto con PyMuPDF o con OCR si es necesario."""
    with fitz.open(pdf_path) as doc:
        final_text = []

        for page_num, page in enumerate(doc):
            text = page.get_text()

            if text and len(text.strip()) > 20:
                final_text.append(text)
            else:
                if OCR_AVAILABLE:
                    # usar OCR
                    pix = page.get_pixmap(dpi=200)
                    img_path = pdf_path.with_suffix(f".page{page_num}.png")
                    pix.save(img_path)
                    ocr_text = pytesseract.image_to_string(Image.open(img_path))
                    final_text.append(ocr_text)
                else:
                    final_text.append("")

    return "\n".join(final_text)


def extract_skus_from_text(text: str) -> List[str]:
    """
    Extrae SKUs siguiendo reglas de Natura y Avon.
    Reglas observadas:
        - 3 a 7 dígitos seguidos: (12345)  178156  64748
        - SKU suele aparecer entre paréntesis o junto al código
        - Eliminamos números que parecen precios (XXX.XX)
    """

    # Encuentra candidatos tipo números puros de 3–7 dígitos
    candidates = re.findall(r"\b(\d{3,7})\b", text)

    skus: Set[str] = set()

    for c in candidates:
        # filtrar números que son precios  (ej: 365, 10800)
        if re.match(r"^\d{1,5}\.\d{2}$", c):
            continue

        # filtrar pesos MX del texto: $365, $144.35
        if len(c) <= 3:
            # muy probablemente no sea SKU (Natura casi siempre usa 5–6 dígitos)
            continue

        skus.add(c)

    # Convertir a lista ordenada
    skus = sorted(list(skus), key=lambda x: int(x))
    return skus


def save_skus(marca: str, ciclo: str, skus: List[str]):
    out_path = OUTPUT_DIR / f"{marca}_{ciclo}_skus.txt"
    with out_path.open("w", encoding="utf-8") as f:
        for s in skus:
            f.write(s + "\n")
    print(f"✔ SKUs guardados en {out_path} ({len(skus)} SKUs)")


# -------------------------------
# MAIN
# -------------------------------

def extract_skus_for_pdf(pdf_path: Path, marca: str, ciclo: str):
    print(f"\n📄 Procesando: {pdf_path.name} ({marca}, ciclo {ciclo})")

    if is_text_pdf(pdf_path):
        print("→ PDF de texto detectado.")
        text = extract_text_from_pdf(pdf_path)
    else:
        print("→ PDF de imagen detectado, usando OCR (si disponible).")
        if OCR_AVAILABLE:
            text = extract_text_from_pdf(pdf_path)
        else:
            raise RuntimeError("Este PDF es imagen y no tienes OCR instalado.")

    print("→ Extrayendo SKUs...")
    skus = extract_skus_from_text(text)

    print(f"→ SKUs detectados: {len(skus)}")
    save_skus(marca, ciclo, skus)


if __name__ == "__main__":
    # EJEMPLOS — AJUSTA ESTO SEGÚN TUS ARCHIVOS
    pdfs = [
        ("Natura", "202516", "input_pdfs/Natura16LB.pdf"),
        ("Avon", "202516", "input_pdfs/AvonBelleza16LB.pdf"),
        ("AvonHogar", "202516", "input_pdfs/AvonHogar16LB.pdf"),
    ]

    for marca, ciclo, path in pdfs:
        path = Path(path)
        if path.exists():
            extract_skus_for_pdf(path, marca, ciclo)
        else:
            print(f"❌ No existe {path}")
