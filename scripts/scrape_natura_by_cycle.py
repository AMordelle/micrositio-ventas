#!/usr/bin/env python3
# scripts/scrape_natura_by_cycle.py

"""
Scraper profesional de productos Natura por ciclo.

Flujo:
    1. Carga lista de SKUs desde TXT (extraídos del PDF).
    2. Abre sesión Natura usando storage_state.
    3. Busca cada SKU con autocomplete.
    4. Si aparece → pertenece al ciclo actual (202516).
    5. Si no aparece → no pertenece / no está disponible.
    6. Guarda:
        - natura_202516.json      (productos válidos)
        - natura_202516_missing.txt  (SKUs no encontrados)
"""

from pathlib import Path
import json
import re
from typing import Dict, Any, List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ------------------------
# CONFIG
# ------------------------

STORAGE_FILE = Path("storage/natura_state.json")
INPUT_SKUS_FILE = Path("output/skus/Natura_202516_skus.txt")

OUTPUT_DIR = Path("output/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "natura_202516.json"
OUTPUT_MISSING = OUTPUT_DIR / "natura_202516_missing.txt"

NEW_ORDER_URL = "https://gsp.natura.com/login?country=MX"
CICLO = "202516"


# ------------------------
# HELPERS
# ------------------------

def parse_price(text: str) -> float | None:
    m = re.search(r"(\d+[\.,]\d{2})", text)
    return float(m.group(1).replace(",", ".")) if m else None


def parse_info_line(text: str) -> Dict[str, Any]:
    parts = [p.strip() for p in text.split("|") if p.strip()]

    brand = parts[0] if parts else None
    sku = None
    points = None

    for part in parts:
        m_sku = re.search(r"cod\.?\s*(\d{3,7})", part, re.I)
        if m_sku:
            sku = m_sku.group(1)

        m_pts = re.search(r"(\d+)\s*pts", part, re.I)
        if m_pts:
            points = int(m_pts.group(1))

    return {"brand": brand, "sku": sku, "points": points}


def extract_autocomplete_item(page) -> Dict[str, Any] | None:
    items = page.locator('[data-testid="autocomplete-items"]')
    if items.count() == 0:
        return None

    item = items.first

    # Imagen
    img = item.locator("img")
    image_url = img.get_attribute("src") if img.count() > 0 else None

    # Nombre
    name = item.locator('[data-testid="item-name"] p').inner_text()

    # Info
    info_text = item.locator('[data-testid="item-info"]').inner_text()
    info = parse_info_line(info_text)

    # Precio compra
    price_block = item.locator('[data-testid="product-price"]')
    price_text = price_block.inner_text() if price_block.count() > 0 else ""
    price_purchase = parse_price(price_text)

    return {
        "brand": info["brand"],
        "sku": info["sku"],
        "name": name,
        "points": info["points"],
        "price_purchase": price_purchase,
        "image_url": image_url,
        "cycle": CICLO,
    }


def scrape_sku(page, sku: str) -> Dict[str, Any] | None:
    print(f"→ Buscando SKU {sku}")

    # Input del buscador
    search_container = page.locator('[data-testid="autocomplete-search"]')

    if search_container.count() == 0:
        print("  ❌ No se encontró el buscador.")
        return None

    input_box = search_container.locator('input[data-testid="ds-input"]')
    input_box.fill("")
    input_box.fill(sku)

    # Dropdown de opciones
    ul_options = search_container.locator('[data-testid="ul-options"]')

    try:
        ul_options.wait_for(timeout=6000)
    except PlaywrightTimeoutError:
        print("  ↳ No apareció el autocomplete (producto no pertenece al ciclo).")
        return None

    product = extract_autocomplete_item(page)

    if not product:
        print("  ↳ Autocomplete vacío.")
        return None

    if product["sku"] != sku:
        print(f"  ↳ El autocomplete devolvió otro SKU ({product['sku']}), descartado.")
        return None

    print(f"  ✔ Encontrado: {product['name']} | ${product['price_purchase']}")
    return product


# ------------------------
# MAIN
# ------------------------

def main():
    if not STORAGE_FILE.exists():
        print(f"❌ No existe {STORAGE_FILE}. Ejecuta natura_login.py primero.")
        return

    if not INPUT_SKUS_FILE.exists():
        print(f"❌ No existe {INPUT_SKUS_FILE}. Ejecuta extract_skus_from_pdf.py primero.")
        return

    # Cargar SKUs desde archivo
    skus = [s.strip() for s in INPUT_SKUS_FILE.read_text().splitlines() if s.strip()]
    print(f"\n📦 SKUs cargados: {len(skus)}")

    products: List[Dict[str, Any]] = []
    missing: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(STORAGE_FILE))
        page = context.new_page()

        print(f"\n🌐 Cargando página del catálogo: {NEW_ORDER_URL}")
        page.goto(NEW_ORDER_URL, timeout=0)

        # Esperar el buscador
        try:
            page.locator('[data-testid="autocomplete-search"]').wait_for(timeout=20000)
            print("✔ Buscador listo.")
        except:
            print("❌ No se detectó el buscador, abortando.")
            return

        # Scrapeo por SKU
        for sku in skus:
            product = scrape_sku(page, sku)
            if product:
                products.append(product)
            else:
                missing.append(sku)

        browser.close()

    # Guardar resultados
    OUTPUT_JSON.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
    OUTPUT_MISSING.write_text("\n".join(missing), encoding="utf-8")

    print("\n=====================================")
    print(f"✔ Productos encontrados: {len(products)}")
    print(f"✔ Guardado en: {OUTPUT_JSON}")
    print(f"✔ SKUs no encontrados: {len(missing)}")
    print(f"✔ Guardado en: {OUTPUT_MISSING}")
    print("=====================================\n")


if __name__ == "__main__":
    main()
