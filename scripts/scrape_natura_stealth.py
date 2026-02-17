#!/usr/bin/env python3
# scripts/scrape_natura_stealth.py

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

# ⚠️ Puedes cambiar esto por tu user-agent real si quieres (DevTools → console → navigator.userAgent)
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36"
)

# ----------------------------------------
# HELPERS
# ----------------------------------------

def wait_human(min_s=0.7, max_s=1.6):
    time.sleep(random.uniform(min_s, max_s))


def parse_price(text: str) -> float | None:
    m = re.search(r"(\d+[\.,]\d{2})", text)
    return float(m.group(1).replace(",", ".")) if m else None


def close_popups(page):
    selectors = [
        '[role="dialog"] button',
        '[data-testid="modal-close-button"]',
        'button:has-text("Cerrar")',
        'button:has-text("Aceptar")',
        'button:has-text("Entendido")',
        'button:has-text("OK")',
        'button:has-text("LISTO")',
        'button:has-text("No")',
    ]
    for sel in selectors:
        btns = page.locator(sel)
        if btns.count() > 0:
            try:
                btns.first.click()
                wait_human(0.2, 0.5)
            except:
                pass


def check_error_banner(page):
    html = page.content().lower()
    for w in ["problemas con", "lo sentimos", "intenta más tarde", "error inesperado"]:
        if w in html:
            return True
    return False


def human_type(locator, text: str):
    locator.click()
    wait_human(0.3, 0.8)
    # borramos lo que haya
    locator.press("Control+A")
    locator.press("Delete")
    wait_human(0.2, 0.5)
    for ch in text:
        locator.type(ch)
        time.sleep(random.uniform(0.05, 0.18))


def human_scroll_and_move(page):
    w = page.viewport_size["width"]
    h = page.viewport_size["height"]

    # mover mouse a algunos puntos
    for _ in range(3):
        x = random.randint(50, w - 50)
        y = random.randint(80, h - 50)
        page.mouse.move(x, y, steps=random.randint(8, 20))
        wait_human(0.1, 0.3)

    # scroll suave
    for _ in range(3):
        delta = random.randint(80, 200)
        page.mouse.wheel(0, delta)
        wait_human(0.15, 0.4)


def autocomplete_has_sku(page, sku: str) -> bool:
    print(f"→ Validando SKU {sku}")

    close_popups(page)
    human_scroll_and_move(page)

    search_container = page.locator('[data-testid="autocomplete-search"]')
    input_box = search_container.locator('input[data-testid="ds-input"]')

    human_type(input_box, sku)

    ul_options = search_container.locator('[data-testid="ul-options"]')

    try:
        ul_options.wait_for(timeout=7000)
        return True
    except PlaywrightTimeoutError:
        print("  ↳ No aparece en autocomplete → fuera del ciclo o no disponible.")
        return False


def scrape_detail(page, sku: str) -> Dict[str, Any] | None:
    url = f"https://gsp.natura.com/showcase/pesquisa?q={sku}&ciclo={CICLO}"
    print(f"  → Detalle: {url}")

    try:
        page.goto(url, timeout=0, wait_until="load")
    except:
        return None

    wait_human(0.8, 1.8)
    human_scroll_and_move(page)
    close_popups(page)

    if check_error_banner(page):
        print("  ⚠ Error banner detectado → reintento suave…")
        close_popups(page)
        wait_human(1.0, 2.0)
        try:
            page.goto(url, timeout=0, wait_until="load")
        except:
            return None
        wait_human(0.8, 1.5)
        close_popups(page)

    card = page.locator(f'[data-testid="card-{sku}"]')

    try:
        card.wait_for(timeout=9000)
    except:
        print("  ❌ No se encontró tarjeta para este SKU.")
        return None

    img = card.locator('[data-testid^="card-header-image"] img')
    brand_sku = card.locator(".CardDescription-brand-7-2-2701 p").inner_text()
    name = card.locator('[data-testid="card-name"] p').inner_text()

    pts_text = card.locator('[data-testid^="card-header-tag-points"]').inner_text()
    m_pts = re.search(r"(\d+)", pts_text)
    points = int(m_pts.group(1)) if m_pts else None

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
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ]
        )

        context = browser.new_context(
            storage_state=str(STORAGE_FILE),
            user_agent=CHROME_UA,
            locale="es-MX",
            viewport={"width": 1366, "height": 768}
        )

        # Script para quitar señales de automatización
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            });

            window.chrome = {
              runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
              get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
              get: () => ['es-MX', 'es', 'en'],
            });
        """)

        page = context.new_page()

        print(f"Abriendo página de nuevo pedido: {NEW_ORDER_URL}")
        page.goto(NEW_ORDER_URL, timeout=0, wait_until="load")
        wait_human(1.5, 3.0)
        human_scroll_and_move(page)
        close_popups(page)

        try:
            page.locator('[data-testid="autocomplete-search"]').wait_for(timeout=25000)
            print("✔ Buscador listo.")
        except:
            print("❌ No se detectó el buscador.")
            browser.close()
            return

        for idx, sku in enumerate(skus, start=1):
            print(f"\n================ SKU {sku} ({idx}/{len(skus)}) ================")

            try:
                close_popups(page)
                wait_human()

                if not autocomplete_has_sku(page, sku):
                    missing.append(sku)
                    continue

                product = scrape_detail(page, sku)
                if not product:
                    print("  ↳ Reintentando SKU una vez más…")
                    wait_human(1.0, 2.0)
                    product = scrape_detail(page, sku)

                if product:
                    products.append(product)
                else:
                    missing.append(sku)

                # pausas entre SKUs para no parecer bot
                wait_human(1.2, 2.5)

            except Exception as e:
                print(f"  ❌ Error inesperado con SKU {sku}: {e}")
                missing.append(sku)
                wait_human(2.0, 4.0)

        browser.close()

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
