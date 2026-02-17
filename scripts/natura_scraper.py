#!/usr/bin/env python3
# scripts/natura_scraper.py

from pathlib import Path
import json
import re
from typing import Dict, Any, List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

STORAGE_FILE = Path("storage/natura_state.json")
OUTPUT_DIR = Path("output/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Página de "Nuevo Pedido" / catálogo natura
NEW_ORDER_URL = "https://gsp.natura.com/login?country=MX"
CICLO = "202516"  # ajusta según el ciclo actual


# -------- helpers de parsing --------

def parse_price(text: str) -> float | None:
    m = re.search(r"(\d+[\.,]\d{2})", text)
    return float(m.group(1).replace(",", ".")) if m else None


def parse_info_line(text: str) -> Dict[str, Any]:
    """
    Ejemplo de text (item-info):
    "Natura | cod. 151023 | 12 pts"
    """
    brand = None
    sku = None
    points = None

    parts = [p.strip() for p in text.split("|") if p.strip()]
    # brand
    if parts:
        brand = parts[0]

    # cod y pts
    for part in parts:
        m_sku = re.search(r"cod\.?\s*(\d{3,7})", part, re.I)
        if m_sku:
            sku = m_sku.group(1)
        m_pts = re.search(r"(\d+)\s*pts", part, re.I)
        if m_pts:
            points = int(m_pts.group(1))

    return {"brand": brand, "sku": sku, "points": points}


# -------- extracción de un resultado del autocomplete --------

def extract_from_autocomplete(page) -> Dict[str, Any] | None:
    """
    Extrae la info del primer resultado del dropdown de autocomplete.
    Asume que ya se escribió un SKU y apareció la lista.
    """
    items = page.locator('[data-testid="autocomplete-items"]')
    if items.count() == 0:
        return None

    item = items.first

    # Imagen
    img = item.locator("img")
    image_url = img.get_attribute("src") if img.count() > 0 else None

    # Nombre
    name = item.locator('[data-testid="item-name"] p').inner_text()

    # Info (marca, cod, puntos)
    info_text = item.locator('[data-testid="item-info"]').inner_text()
    info = parse_info_line(info_text)

    # Precio (Compra)
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


# -------- lógica por SKU --------

def scrape_sku(page, sku: str) -> Dict[str, Any] | None:
    print(f"\n→ Buscando SKU {sku}")

    # Input del autocomplete
    search_container = page.locator('[data-testid="autocomplete-search"]')
    input_box = search_container.locator('input[data-testid="ds-input"]')

    # Limpiar input, escribir SKU
    input_box.fill("")
    input_box.fill(sku)

    # Esperar a que aparezca la lista de opciones
    ul_options = search_container.locator('[data-testid="ul-options"]')
    try:
        ul_options.wait_for(timeout=8000)
    except PlaywrightTimeoutError:
        print("  ⚠ No apareció el dropdown de autocomplete.")
        return None

    product = extract_from_autocomplete(page)
    if not product:
        print("  ⚠ No se encontró ningún item en el autocomplete.")
        return None

    if product["sku"] != sku:
        print(f"  ⚠ El autocomplete devolvió SKU {product['sku']}, no coincide con {sku}.")
        return None

    print(f"  ✔ {product['name']} | Compra: {product['price_purchase']} | pts: {product['points']}")
    return product


# -------- main --------

def main():
    if not STORAGE_FILE.exists():
        print(f"❌ No se encontró {STORAGE_FILE}. Corre primero scripts/natura_login.py")
        return

    # SKUs a probar (luego puedes cargar desde archivo o generar lista)
    skus: List[str] = [
        "151023",
        "64748",
        # agrega más SKUs aquí...
    ]

    all_products: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(STORAGE_FILE))

        page = context.new_page()
        print(f"Abriendo página de nuevo pedido: {NEW_ORDER_URL}")
        page.goto(NEW_ORDER_URL, timeout=0)

        # NATURA nunca llega a 'networkidle', así que esperamos al buscador directo
        print("Esperando la carga del buscador...")
        try:
            page.locator('[data-testid="autocomplete-search"]').wait_for(timeout=20000)
            print("✔ Buscador detectado.")
        except:
            print("⚠ No se detectó el buscador. Revisando si hay popups...")
            browser.close()
            return

        # Scraping por SKU
        for sku in skus:
            prod = scrape_sku(page, sku)
            if prod:
                all_products.append(prod)

        browser.close()

    out_file = OUTPUT_DIR / "natura_scraped.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Archivo generado: {out_file}")
    print(f"✅ Productos totales: {len(all_products)}")


if __name__ == "__main__":
    main()
