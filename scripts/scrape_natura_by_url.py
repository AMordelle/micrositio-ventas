#!/usr/bin/env python3
# scripts/scrape_natura_by_url.py
"""
Scraper por URL directa:
Para cada SKU hace:
  https://gsp.natura.com/showcase/pesquisa?q=<SKU>&ciclo=202517

No usa el buscador ni el flujo de "Nuevo Pedido", así evitamos
redirecciones al carrito y cualquier comportamiento raro.
"""

from pathlib import Path
import json
import re
import time
from typing import Dict, Any, List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

CICLO = "202517"

STORAGE_FILE = Path("storage/natura_state.json")
INPUT_SKUS_FILE = Path("output/skus/all_skus_202517.json")

OUTPUT_DIR = Path("output/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / f"natura_{CICLO}.json"
OUTPUT_MISSING = OUTPUT_DIR / f"natura_{CICLO}_missing.txt"

# Opcional: ajusta si quieres más/menos pausa entre SKUs
MIN_DELAY = 0.6
MAX_DELAY = 1.6

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def human_wait(min_s: float = MIN_DELAY, max_s: float = MAX_DELAY):
    import random
    time.sleep(random.uniform(min_s, max_s))


def parse_price(text: str) -> float | None:
    """
    Extrae el primer 999.99 o 999,99 del texto.
    """
    m = re.search(r"(\d+[\.,]\d{2})", text)
    return float(m.group(1).replace(",", ".")) if m else None


def scrape_sku_page(page, sku: str) -> Dict[str, Any] | None:
    """
    Carga la página de detalle por URL directa y extrae:
    - brand
    - sku
    - name
    - points
    - price_purchase
    - price_sale
    - image_url
    - cycle
    - category (por ahora None)
    """
    url = f"https://gsp.natura.com/showcase/pesquisa?q={sku}&ciclo={CICLO}"
    print(f"  → GET {url}")

    try:
        page.goto(url, timeout=0, wait_until="load")
    except Exception as e:
        print(f"  ⚠ Error en goto: {e}")
        return None

    # Buscamos la tarjeta principal del SKU
    card = page.locator(f'[data-testid="card-{sku}"]')

    try:
        card.wait_for(timeout=9000)
    except PlaywrightTimeoutError:
        print("  ⚠ No se encontró tarjeta para este SKU (quizá fuera del ciclo).")
        return None

    # Imagen
    img = card.locator('[data-testid^="card-header-image"] img')
    image_url = img.get_attribute("src") if img.count() > 0 else None

    # Marca + SKU (ej: "Natura | cod. 160216")
    brand_line = card.locator(".CardDescription-brand-7-2-2701 p").inner_text().strip()
    # nombre del producto
    name = card.locator('[data-testid="card-name"] p').inner_text().strip()

    # puntos (ej: "10 pts")
    pts_text = card.locator('[data-testid^="card-header-tag-points"]').inner_text()
    m_pts = re.search(r"(\d+)", pts_text)
    points = int(m_pts.group(1)) if m_pts else None

    # precios
    purchase_text = card.locator(
        '[data-testid^="purchasePrice"] p'
    ).last.inner_text()

    resale_text = card.locator(
        '[data-testid^="resalePrice"] p'
    ).last.inner_text()

    product: Dict[str, Any] = {
        "brand": brand_line.split("|")[0].strip(),
        "sku": sku,
        "name": name,
        "points": points,
        "price_purchase": parse_price(purchase_text),
        "price_sale": parse_price(resale_text),
        "image_url": image_url,
        "cycle": CICLO,
        "category": None,  # lo llenaremos más adelante por reglas
    }

    print(
        f"  ✔ {product['name']} | Compra: {product['price_purchase']} | "
        f"Venta: {product['price_sale']} | pts: {product['points']}"
    )
    return product


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main():
    if not STORAGE_FILE.exists():
        print("❌ Falta storage/natura_state.json. Corre primero scripts/natura_login.py")
        return

    if not INPUT_SKUS_FILE.exists():
        print(f"❌ Falta archivo de SKUs: {INPUT_SKUS_FILE}")
        print("   Asegúrate de haber corrido el extractor de PDFs para el ciclo 202517.")
        return

    # Cargamos SKUs desde el JSON maestro
    data = json.loads(INPUT_SKUS_FILE.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "skus" in data:
        skus: List[str] = data["skus"]
    elif isinstance(data, list):
        skus = [str(x) for x in data]
    else:
        print("❌ Formato inesperado en el archivo de SKUs.")
        return

    print(f"📦 Total de SKUs a procesar: {len(skus)}")

    products: List[Dict[str, Any]] = []
    missing: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            storage_state=str(STORAGE_FILE),
            locale="es-MX",
            viewport={"width": 1366, "height": 768},
        )

        page = context.new_page()

        for idx, sku in enumerate(skus, start=1):
            print(f"\n========== [{idx}/{len(skus)}] SKU {sku} ==========")

            try:
                product = scrape_sku_page(page, sku)
                if product:
                    products.append(product)
                else:
                    missing.append(sku)

            except Exception as e:
                print(f"  ❌ Error inesperado con SKU {sku}: {e}")
                missing.append(sku)

            human_wait()

        browser.close()

    # Guardamos resultados
    OUTPUT_JSON.write_text(
        json.dumps(products, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    OUTPUT_MISSING.write_text("\n".join(missing), encoding="utf-8")

    print("\n=============================")
    print(f"✔ Productos descargados: {len(products)}")
    print(f"✔ SKUs sin tarjeta / fuera del ciclo: {len(missing)}")
    print(f"✔ Catálogo guardado en: {OUTPUT_JSON}")
    print(f"✔ Faltantes guardados en: {OUTPUT_MISSING}")
    print("=============================\n")


if __name__ == "__main__":
    main()
