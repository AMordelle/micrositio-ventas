#!/usr/bin/env python3
"""Aplica overrides de promociones PDF sobre el catálogo scrapeado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def pick_catalog_input(cycle: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)

    final_catalog = Path(f"output/data/catalogo_{cycle}_final.json")
    base_catalog = Path(f"output/data/catalogo_{cycle}.json")

    if final_catalog.exists():
        return final_catalog
    if base_catalog.exists():
        return base_catalog
    raise FileNotFoundError(f"No se encontró catálogo base para ciclo {cycle}")


def pick_catalog_output(cycle: str, catalog_input: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)

    if catalog_input.name == f"catalogo_{cycle}_final.json":
        return Path(f"output/data/catalogo_{cycle}_final_with_pdf.json")
    return Path(f"output/data/catalogo_{cycle}_final.json")


def load_promos_by_sku(path: Path) -> Dict[str, Dict]:
    promos = json.loads(path.read_text(encoding="utf-8"))
    by_sku: Dict[str, Dict] = {}
    for item in promos:
        sku = str(item.get("sku", "")).strip()
        if not sku:
            continue
        current = by_sku.get(sku)
        if current is None:
            by_sku[sku] = item
            continue
        current_has_price = current.get("price_sale_final") is not None
        item_has_price = item.get("price_sale_final") is not None
        if item_has_price and not current_has_price:
            by_sku[sku] = item
    return by_sku


def apply_overrides(catalog: List[Dict], promos_by_sku: Dict[str, Dict]) -> tuple[List[Dict], int, int]:
    matched = 0
    for item in catalog:
        sku = str(item.get("sku", "")).strip()
        promo = promos_by_sku.get(sku)
        if not promo:
            continue

        matched += 1

        # Regla de overwrite: SOLO campos de promo de venta al cliente.
        # - NO tocamos name, image_url, brand, points, price_purchase u otros.
        if promo.get("price_sale_final") is not None:
            item["price_sale_final"] = promo["price_sale_final"]
            # Compatibilidad con micrositio: apuntar price_sale al final actualizado.
            item["price_sale"] = promo["price_sale_final"]

        if promo.get("discount_percent") is not None:
            item["discount_percent"] = promo["discount_percent"]

    unmatched = max(0, len(promos_by_sku) - matched)
    return catalog, matched, unmatched


def main() -> None:
    parser = argparse.ArgumentParser(description="Aplica promos de PDF sobre catálogo")
    parser.add_argument("--cycle", required=True, help="Ciclo actual (ej. 202517)")
    parser.add_argument("--promos", default=None, help="Ruta a promos_from_pdf_<cycle>.json")
    parser.add_argument("--catalog-in", default=None, help="Catálogo base de entrada")
    parser.add_argument("--out", default=None, help="Ruta del catálogo final actualizado")
    args = parser.parse_args()

    promos_path = Path(args.promos) if args.promos else Path(f"output/data/promos_from_pdf_{args.cycle}.json")
    catalog_in = pick_catalog_input(args.cycle, args.catalog_in)
    catalog_out = pick_catalog_output(args.cycle, catalog_in, args.out)

    if not promos_path.exists():
        raise FileNotFoundError(f"No existe archivo de promos PDF: {promos_path}")

    catalog = json.loads(catalog_in.read_text(encoding="utf-8"))
    promos_by_sku = load_promos_by_sku(promos_path)

    updated_catalog, matched, unmatched = apply_overrides(catalog, promos_by_sku)

    catalog_out.parent.mkdir(parents=True, exist_ok=True)
    catalog_out.write_text(json.dumps(updated_catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n✅ Aplicación de promos PDF completada")
    print(f"   • Catálogo leído: {catalog_in}")
    print(f"   • Promos detectadas en PDF: {len(promos_by_sku)}")
    print(f"   • SKUs con match en catálogo: {matched}")
    print(f"   • SKUs sin match: {unmatched}")
    print(f"   • Catálogo final actualizado: {catalog_out}")


if __name__ == "__main__":
    main()
