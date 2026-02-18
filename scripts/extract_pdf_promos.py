#!/usr/bin/env python3
"""Extrae promociones (SKU + precio final + descuento) desde PDFs editoriales."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import fitz

SKU_RE = re.compile(r"\b(\d{4,8})\b")
DISCOUNT_RE = re.compile(r"\b(\d{1,2})\s*%\s*de\s*descuento\b", re.IGNORECASE)
DE_A_RE = re.compile(
    r"de\s*\$?\s*([0-9][0-9\.,]*)\s*a\s*\$?\s*([0-9][0-9\.,]*)",
    re.IGNORECASE,
)
A_PRICE_RE = re.compile(r"\ba\s*\$\s*([0-9][0-9\.,]*)", re.IGNORECASE)
DOLLAR_PRICE_RE = re.compile(r"\$\s*([0-9][0-9\.,]*)")


@dataclass
class TextBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def y_mid(self) -> float:
        return (self.y0 + self.y1) / 2


def parse_amount(raw: str) -> Optional[float]:
    value = raw.strip().replace(" ", "")
    if not value:
        return None

    if "," in value and "." in value:
        # 10,999.50 o 10.999,50
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        parts = value.split(",")
        if len(parts[-1]) == 2:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "." in value:
        parts = value.split(".")
        if len(parts[-1]) == 3:
            value = value.replace(".", "")

    try:
        return float(value)
    except ValueError:
        return None


def find_price_sale_final(text: str) -> Optional[float]:
    de_a_match = DE_A_RE.search(text)
    if de_a_match:
        return parse_amount(de_a_match.group(2))

    a_match = A_PRICE_RE.search(text)
    if a_match:
        return parse_amount(a_match.group(1))

    # fallback para bloques de set/promoción con solo "$XXX"
    dollar_matches = DOLLAR_PRICE_RE.findall(text)
    parsed = [parse_amount(x) for x in dollar_matches]
    parsed = [x for x in parsed if x is not None]
    if parsed:
        return parsed[-1]

    return None


def find_discount_percent(text: str) -> Optional[int]:
    match = DISCOUNT_RE.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def extract_blocks(page: fitz.Page) -> List[TextBlock]:
    blocks: List[TextBlock] = []
    for item in page.get_text("blocks"):
        x0, y0, x1, y1, text = item[:5]
        clean = (text or "").strip()
        if not clean:
            continue
        blocks.append(TextBlock(x0=x0, y0=y0, x1=x1, y1=y1, text=clean))
    return blocks


def find_nearest(blocks: List[TextBlock], sku_block: TextBlock, max_vertical_gap: float = 170.0) -> Optional[TextBlock]:
    scored = sorted(blocks, key=lambda b: (abs(b.y_mid - sku_block.y_mid), abs(b.x0 - sku_block.x0)))
    if not scored:
        return None
    best = scored[0]
    if abs(best.y_mid - sku_block.y_mid) > max_vertical_gap:
        return None
    return best


def extract_promos_from_pdf(pdf_path: Path) -> List[Dict]:
    promos: Dict[str, Dict] = {}
    with fitz.open(pdf_path) as doc:
        for page_idx, page in enumerate(doc):
            blocks = extract_blocks(page)
            sku_blocks: List[tuple[TextBlock, str]] = []
            promo_blocks: List[TextBlock] = []

            for block in blocks:
                skus = SKU_RE.findall(block.text)
                if skus:
                    for sku in skus:
                        sku_blocks.append((block, sku))

                if find_price_sale_final(block.text) is not None or find_discount_percent(block.text) is not None:
                    promo_blocks.append(block)

            for sku_block, sku in sku_blocks:
                same_block_price = find_price_sale_final(sku_block.text)
                same_block_discount = find_discount_percent(sku_block.text)

                if same_block_price is None and same_block_discount is None:
                    nearest = find_nearest(promo_blocks, sku_block)
                    if nearest is not None:
                        same_block_price = find_price_sale_final(nearest.text)
                        same_block_discount = find_discount_percent(nearest.text)

                if same_block_price is None and same_block_discount is None:
                    continue

                current = promos.get(sku)
                candidate = {
                    "sku": sku,
                    "price_sale_final": same_block_price,
                    "discount_percent": same_block_discount,
                    "source_pdf": pdf_path.name,
                    "source_page": page_idx + 1,
                }

                # Preferimos candidatos con precio final (más útil para overwrite).
                if current is None:
                    promos[sku] = candidate
                else:
                    current_has_price = current.get("price_sale_final") is not None
                    candidate_has_price = candidate.get("price_sale_final") is not None
                    if candidate_has_price and not current_has_price:
                        promos[sku] = candidate

    return list(promos.values())


def resolve_output_path(cycle: str, out: Optional[Path]) -> Path:
    if out:
        return out
    return Path("output/data") / f"promos_from_pdf_{cycle}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae promociones desde PDFs del ciclo")
    parser.add_argument("--cycle", required=True, help="Ciclo actual (ej. 202517)")
    parser.add_argument("--pdf-dir", default="input_pdfs", help="Directorio con PDFs")
    parser.add_argument("--out", default=None, help="Ruta del JSON de salida")
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    out_path = resolve_output_path(args.cycle, Path(args.out) if args.out else None)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No hay PDFs para procesar en {pdf_dir}")

    all_promos: Dict[str, Dict] = {}
    print(f"📚 PDFs a procesar: {len(pdfs)}")

    for pdf in pdfs:
        print(f"📄 Extrayendo promos de {pdf.name}")
        promos = extract_promos_from_pdf(pdf)
        print(f"   ↳ promos detectadas en archivo: {len(promos)}")
        for promo in promos:
            sku = promo["sku"]
            existing = all_promos.get(sku)
            if existing is None:
                all_promos[sku] = promo
                continue
            existing_has_price = existing.get("price_sale_final") is not None
            promo_has_price = promo.get("price_sale_final") is not None
            if promo_has_price and not existing_has_price:
                all_promos[sku] = promo

    promos_list = sorted(all_promos.values(), key=lambda item: int(item["sku"]))
    out_path.write_text(json.dumps(promos_list, indent=2, ensure_ascii=False), encoding="utf-8")

    with_price = sum(1 for item in promos_list if item.get("price_sale_final") is not None)
    with_discount = sum(1 for item in promos_list if item.get("discount_percent") is not None)

    print("\n✅ Extracción de promos PDF completada")
    print(f"   • Promos únicas detectadas: {len(promos_list)}")
    print(f"   • Con price_sale_final: {with_price}")
    print(f"   • Con discount_percent: {with_discount}")
    print(f"   • Archivo generado: {out_path}")


if __name__ == "__main__":
    main()
