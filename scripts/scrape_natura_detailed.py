#!/usr/bin/env python3
# scripts/scrape_natura_detailed.py

from pathlib import Path
import json
import re
import time
import random
from typing import Dict, Any, List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ----------------------------------------
# CONFIG
# ----------------------------------------

STORAGE_FILE = Path("storage/natura_state.json")
INPUT_SKUS_FILE = Path("output/skus/all_skus_202517.json")

OUTPUT_DIR = Path("output/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "natura_202517.json"
OUTPUT_MISSING = OUTPUT_DIR / "natura_202517_missing.txt"

NEW_ORDER_URL = "https://gsp.natura.com/login?country=MX"
CICLO = "202517"


# ----------------------------------------
# HELPERS
# ----------------------------------------

def wait_human(min_s=0.6, max_s=1.3):
    """Pausa aleatoria tipo humano."""
    time.sleep(random.uniform(min_s, max_s))


def parse_price(text: str) -> float | None:
    m = re.search(r"(\d+[\.,]\d{2})", text)
    return float(m.group(1).replace(",", ".")) if m else None


def close_popups(page):
    """Cierra popups comunes del sitio Natura."""
    selectors = [
        '[role="dialog"] button',
        '[data-testid="modal-close-button"]',
        'button:has-text("Cerrar")',
        'button:has-text("Aceptar")',
        'button:has-text("Entendido")',
        'button:has-text("OK")',
        'button:has-text("Listo")',
        'button:has-text("No")',
    ]

    for sel in selectors:
        btns = page.locator(sel)
        if btns.count() > 0:
            try:
                btns.first.click()
                time.sleep(0.3)
            except:
                pass


def check_error_banner(page):
    """Detecta mensajes de error del sitio."""
    texto = page.content().lower()
    warnings = [
        "problemas con",
        "lo sentimos",
        "intenta más tarde",
        "error inesperado",
        "no se puede procesar"
    ]
    return any(w in texto for w in warnings)


def autocomplete_has_sku(page, sku: str) -> bool:
    """Verifica si el SKU aparece en el autocomplete (indica que está en el ciclo actual)."""
    print(f"→ Validando SKU {sku}")

    close_popups(page)

    search_container = page.locator('[data-testid="autocomplete-search"]')
    input_box = search_container.locator('input[data-testid="ds-input"]')

    input_box.fill("")
    wait_human()
    input_box.fill(sku)

    ul_options = search_container.locator('[data-testid="ul-options"]')

    try:
        ul_options.wait_for(timeout=5000)
        return True
    except PlaywrightTimeoutError:
        print("  ↳ No aparece en autocomplete → fuera del ciclo o no disponible.")
        return False


def scrape_detail(page, sku: str) -> Dict[str, Any] | None:
    """Scrapea la tarjeta de detalle en /pesquisa?q=SKU&ciclo=CICLO."""
    url = f"https://gsp.natura.com/showcase/pesquisa?q={sku}&ciclo={CICLO}"
    print(f"  → Detalle: {url}")

    try:
        page.goto(url, timeout=0)
    except:
        return None

    wait_human()
    close_popups(page)

    if check_error_banner(page):
        print("  ⚠ Error banner detectado → reiniciando página…")
        close_popups(page)
        time.sleep(2)
        page.goto(url, timeout=0)
        close_popups(page)

    card = page.locator(f'[data-testid="card-{sku}"]')

    try:
        card.wait_for(timeout=8000)
    except:
        print("  ❌ No se encontró tarjeta para este SKU.")
        return None

    # Imagen
    img = card.locator('[data-testid^="card-header-image"] img')

    # Marca y SKU (ej: "Natura | cod. 160216")
    brand_sku = card.locator(".CardDescription-brand-7-2-2701 p").inner_text()

    # Nombre
    name = card.locator('[data-testid="card-name"] p').inner_text()

    # Puntos (ej: "10 pts")
    pts_text = card.locator('[data-testid^="card-header-tag-points"]').inner_text()
    m_pts = re.search(r"(\d+)", pts_text)
    points = int(m_pts.group(1)) if m_pts else None

    # Precios
    purchase = card.locator('[data-testid^="purchasePrice"] p:last-of-type').inner_text()
    resale = card.locator('[data-testid^="resalePrice"] p:last-of-type').inner_text()

    product = {
        "sku": sku,
        "brand": brand_sku.split("|")[0].strip(),
        "name": name.strip(),
        "points": points,
        "price_purchase": parse_price(purchase),
        "price_sale": parse_price(resale),
        "image_url": img.get_attribute("src") if img.count() > 0 else None,
        "cycle": CICLO,
        # category: por ahora la dejamos para un paso posterior
        "category": None
    }

    print(f"  ✔ {product['name']} | Compra: {product['price_purchase']} | Venta: {product['price_sale']}")
    return product


def main():
    if not STORAGE_FILE.exists():
        print("❌ Falta sesión guardada (storage/natura_state.json). Corre scripts/natura_login.py primero.")
        return

    if not INPUT_SKUS_FILE.exists():
        print("❌ Falta archivo maestro de SKUs (output/skus/all_skus_202517.json).")
        return

    data = json.loads(INPUT_SKUS_FILE.read_text(encoding="utf-8"))
    skus = data["skus"]

    print(f"📦 Total SKUs a procesar: {len(skus)}")

    products: List[Dict[str, Any]] = []
    missing: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(STORAGE_FILE))
        page = context.new_page()

        print(f"Abriendo página de nuevo pedido: {NEW_ORDER_URL}")
        page.goto(NEW_ORDER_URL, timeout=0)
        close_popups(page)

        try:
            page.locator('[data-testid="autocomplete-search"]').wait_for(timeout=25000)
            print("✔ Buscador listo.")
        except:
            print("❌ No se detectó el buscador.")
            browser.close()
            return

        for sku in skus:
            close_popups(page)
            wait_human()

            # 1) Validar que el SKU esté disponible en autocomplete (ciclo actual)
            if not autocomplete_has_sku(page, sku):
                missing.append(sku)
                continue

            # 2) Scraping de detalle con retry
            product = scrape_detail(page, sku)
            if not product:
                print("  ↳ Reintentando SKU…")
                time.sleep(2)
                product = scrape_detail(page, sku)

            if product:
                products.append(product)
            else:
                missing.append(sku)

        browser.close()

    # Guardar resultados
    OUTPUT_JSON.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
    OUTPUT_MISSING.write_text("\n".join(missing), encoding="utf-8")

    print("\n===============================")
    print(f"✔ Productos descargados: {len(products)}")
    print(f"✔ SKUs sin producto / fuera del ciclo: {len(missing)}")
    print(f"✔ Guardado catálogo: {OUTPUT_JSON}")
    print(f"✔ Guardado faltantes: {OUTPUT_MISSING}")
    print("===============================\n")


if __name__ == "__main__":
    main()
