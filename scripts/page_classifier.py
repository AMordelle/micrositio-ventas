#!/usr/bin/env python3
"""
scripts/page_classifier.py

Escanea todos los PDFs en input_pdfs/, extrae texto por página y clasifica cada página
según reglas heurísticas (producto simple, tonos/sku-list, De->A ofertas, combo, legal, banner, vacío, etc).

Salida:
 - output/page_classification/<pdf_name>.json  # detalles por página
 - output/page_classification/summary.json     # conteo global por tipo
 - output/page_classification/summary.csv      # versión CSV

Uso:
    python scripts/page_classifier.py
"""

import re
import json
import csv
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, Any, List

# Intentar usar el extractor ya creado; si no, fallback a PyMuPDF directo.
try:
    from pipeline.extract.extract_pipeline import extract_pdf
    HAS_PIPELINE_EXTRACT = True
except Exception:
    HAS_PIPELINE_EXTRACT = False
    import fitz  # PyMuPDF

OUTPUT_DIR = Path("output/page_classification")
INPUT_DIR = Path("input_pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# Patrones compilados
# -------------------------
RE_SKU_PARENS = re.compile(r"\(\s*\d{3,7}\s*\)")                 # (12345)
RE_SKU_INLINE = re.compile(r"\b\d{3,7}\b")                      # 12345 possibly alone
RE_PRICE = re.compile(r"\$?\s*\d{1,3}(?:[.,]\d{2})?")           # $ 123.00 or 123.00
RE_DE_A_1 = re.compile(r"\bDe[:\s]*\$?\s*\d{1,3}(?:[.,]\d{2})?", re.I)
RE_DE_A_2 = re.compile(r"\bA[:\s]*\$?\s*\d{1,3}(?:[.,]\d{2})?", re.I)
RE_PERCENT = re.compile(r"(\d{1,3})\s*%")
RE_PROMO_TAG = re.compile(r"\b(OFERTA|PROMOCIÓN|PROMO|MEGA|SUPER PROMO|SUPER PROMOCION|MEGAOFERTA)\b", re.I)
RE_COMBO = re.compile(r"\b(Combo|Set|Kit|Incluye|Paquete)\b", re.I)
RE_LEGAL = re.compile(r"\b(COFEPRIS|PROMOCI[oó]n v[aá]lida|Promoci[oó]n v[aá]lida|Promoción válida|Promoción válida hasta|Aviso COFEPRIS|Promoción válida únicamente)\b", re.I)
RE_TONE_LIST_LINE = re.compile(r".*\(\s*\d{3,7}\s*\)\s*$")      # lines that end with (12345)
RE_POINTS = re.compile(r"\b\d+\s+pts\b", re.I)
RE_PRICE_LINE_ALONE = re.compile(r"^\s*\$?\s*\d{1,3}(?:[.,]\d{2})?\s*$")

# -------------------------
# Clasificador de página
# -------------------------
def classify_page(text: str) -> Dict[str, Any]:
    """
    Clasifica una página y extrae metadatos útiles.
    Devuelve dict con:
      - detected_type
      - skus_found (list)
      - prices_found (list)
      - percent_found (list)
      - points_found (bool)
      - summary (short)
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = "\n".join(lines)

    skus = RE_SKU_PARENS.findall(joined)
    skus_inline = RE_SKU_INLINE.findall(joined)
    # filtro mínimo: si paréntesis detectados, prefierelos; si no, tomar numericos que aparezcan con contexto
    skus_norm = list(dict.fromkeys([s.strip("() ").strip() for s in skus]))  # uniq order-preserving
    if not skus_norm:
        # filtrar números que parecen SKU (pero evitar años, largos, etc)
        maybe = []
        for token in skus_inline:
            if len(token) >= 3 and len(token) <= 7:
                maybe.append(token)
        skus_norm = list(dict.fromkeys(maybe))

    prices = RE_PRICE.findall(joined)
    percents = RE_PERCENT.findall(joined)
    has_points = bool(RE_POINTS.search(joined))
    has_promo_tag = bool(RE_PROMO_TAG.search(joined))
    has_combo = bool(RE_COMBO.search(joined))
    has_legal = bool(RE_LEGAL.search(joined))

    # heurísticas para detectar tipos
    # 1) EMPTY
    if len(lines) == 0:
        dtype = "EMPTY"

    # 2) LEGAL / BANNER (texto sin skus ni precios y contiene legal keywords)
    elif has_legal and not skus_norm and not prices:
        dtype = "LEGAL"

    # 3) PAGE PROMO / BANNER (promo words but no sku)
    elif has_promo_tag and not skus_norm:
        dtype = "PROMO_BANNER"

    # 4) COMBO (presence of 'Combo' or multiple '-' or 'Incluye')
    elif has_combo:
        dtype = "COMBO"

    # 5) MANY_TONES / SKU LIST (lines with many "(nnn)" occurrences or many sku-like tokens)
    else:
        # contar cuántas líneas terminan en (12345)
        tone_lines = sum(1 for ln in lines if RE_TONE_LIST_LINE.match(ln))
        sku_count = len(skus_norm)
        # If many sku-like lines or many sku tokens in page -> TONES_LIST
        if tone_lines >= 3 or sku_count >= 6:
            dtype = "TONES_LIST"
        # If there is "De" and "A" or pattern like "De: ... A: ..." => DE_TO_A
        elif RE_DE_A_1.search(joined) or RE_DE_A_2.search(joined):
            dtype = "DE_TO_A"
        # If there's at least one sku and at least one price on same page -> PRODUCT_SIMPLE
        elif sku_count >= 1 and prices:
            dtype = "PRODUCT_SIMPLE"
        # If there's just SKUs but no prices (catalogo de tonos sin precio)
        elif sku_count >= 1 and not prices:
            dtype = "SKU_ONLY"
        # fallback: if promo tag + percent
        elif has_promo_tag and percents:
            dtype = "PROMO_BANNER"
        else:
            dtype = "UNKNOWN"

    summary = []
    if skus_norm:
        summary.append(f"skus={len(skus_norm)}")
    if prices:
        summary.append(f"prices={len(prices)}")
    if percents:
        summary.append(f"discounts={','.join(percents)}")
    if has_points:
        summary.append("points")
    if has_combo:
        summary.append("combo")
    if has_legal:
        summary.append("legal")

    return {
        "detected_type": dtype,
        "skus_found": skus_norm,
        "prices_found": prices,
        "percent_found": percents,
        "points_found": has_points,
        "summary": "; ".join(summary),
        "line_count": len(lines),
        "sample": (lines[:6] if len(lines) >= 6 else lines)
    }

# -------------------------
# Utils: extracción fallback con PyMuPDF
# -------------------------
def extract_pages_with_pymupdf(pdf_path: Path) -> Dict[int, str]:
    doc = fitz.open(str(pdf_path))
    pages = {}
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages[i+1] = text or ""
    doc.close()
    return pages

# -------------------------
# Runner principal
# -------------------------
def process_pdf(pdf_path: Path) -> Dict[str, Any]:
    print(f"Processing {pdf_path.name} ...")
    if HAS_PIPELINE_EXTRACT:
        try:
            pages = extract_pdf(str(pdf_path))
        except Exception as e:
            print(f"Warning: pipeline.extract failed for {pdf_path.name}: {e}. Falling back to PyMuPDF.")
            pages = extract_pages_with_pymupdf(pdf_path)
    else:
        pages = extract_pages_with_pymupdf(pdf_path)

    per_page = {}
    counts = Counter()
    for page_num, text in pages.items():
        info = classify_page(text)
        per_page[page_num] = info
        counts[info["detected_type"]] += 1

    result = {
        "pdf": pdf_path.name,
        "total_pages": len(pages),
        "counts": dict(counts),
        "pages": per_page
    }

    # save per-pdf json
    out_file = OUTPUT_DIR / f"{pdf_path.stem}_classification.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f" - Saved {out_file}")

    return result

# -------------------------
# Main
# -------------------------
def main():
    pdfs = sorted([p for p in INPUT_DIR.glob("*.pdf")])
    if not pdfs:
        print("No PDFs found in input_pdfs/. Coloca los catálogos allí y vuelve a ejecutar.")
        return

    all_results = []
    global_counter = Counter()
    summary_rows = []

    for pdf in pdfs:
        res = process_pdf(pdf)
        all_results.append(res)
        for k, v in res["counts"].items():
            global_counter[k] += v

        # Build CSV rows per pdf-type counts
        row = {"pdf": res["pdf"], "total_pages": res["total_pages"]}
        for t, c in res["counts"].items():
            row[t] = c
        summary_rows.append(row)

    # Save consolidated JSON
    consolidated = {
        "total_pdfs": len(pdfs),
        "global_counts": dict(global_counter),
        "per_pdf": [{ "pdf": r["pdf"], "counts": r["counts"], "total_pages": r["total_pages"] } for r in all_results]
    }
    summary_json = OUTPUT_DIR / "summary.json"
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    print(f"Saved consolidated summary: {summary_json}")

    # Save CSV (rows might have variable columns; union all keys)
    csv_file = OUTPUT_DIR / "summary.csv"
    # collect all possible keys
    keys = set()
    for r in summary_rows:
        keys.update(r.keys())
    keys = ["pdf", "total_pages"] + sorted(k for k in keys if k not in ("pdf", "total_pages"))
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in summary_rows:
            writer.writerow(r)
    print(f"Saved CSV: {csv_file}")

    # print quick report
    print("\n=== GLOBAL REPORT ===")
    for k, v in global_counter.most_common():
        print(f"{k:20s} : {v}")

if __name__ == "__main__":
    main()
