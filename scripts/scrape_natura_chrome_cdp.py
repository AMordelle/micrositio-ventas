#!/usr/bin/env python3
# scripts/scrape_natura_chrome_cdp.py

import argparse
import json
import random
import re
import time
from pathlib import Path
from typing import Dict, List, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ======================================================
# PARSEO DE PRECIOS
# ======================================================

def parse_price(text: str) -> float | None:
    m = re.search(r"(\d[0-9\.,]*\d)", text)
    if not m:
        return None

    num = m.group(1)
    has_dot = "." in num
    has_comma = "," in num

    # PUNTO + COMA
    if has_dot and has_comma:
        first_dot = num.find(".")
        first_comma = num.find(",")

        if first_dot < first_comma:
            # 1.169,00 → miles . / decimal ,
            num = num.replace(".", "").replace(",", ".")
        else:
            # 1,169.00 → miles , / decimal .
            num = num.replace(",", "")
        return float(num)

    # SOLO COMA
    if has_comma:
        parts = num.split(",")
        if len(parts[-1]) == 3:  # miles
            return float(num.replace(",", ""))
        return float(num.replace(",", "."))

    # SOLO PUNTO
    if has_dot:
        parts = num.split(".")
        if len(parts[-1]) == 3:  # miles
            return float(num.replace(".", ""))
        return float(num)

    # SOLO DÍGITOS
    return float(num)

# ======================================================
# HELPERS
# ======================================================

def ensure_search_bar(page) -> bool:
    return page.locator('[data-testid="autocomplete-search"]').count() > 0


def detect_session_lost(page, sku=None) -> bool:
    url = page.url
    if ("natura-auth" in url or "login" in url) and "showcase" not in url:
        print(f"  ❌ Sesión perdida (URL={url}) {f'SKU={sku}' if sku else ''}")
        return True

    if not ensure_search_bar(page) and "showcase" not in url:
        print(f"  ❌ Página sin buscador y fuera de showcase {f'SKU={sku}' if sku else ''}")
        return True

    return False

# ======================================================
# BÚSQUEDA + TARJETA
# ======================================================

def search_and_open_results(page, sku: str) -> bool:
    print(f"  🔍 Buscando SKU {sku}...")

    if not ensure_search_bar(page):
        return False

    container = page.locator('[data-testid="autocomplete-search"]')
    input_box = container.locator('input[data-testid="ds-input"]')

    try:
        input_box.fill("")
        input_box.fill(sku)
    except:
        return False

    ul = container.locator('[data-testid="ul-options"] li')

    try:
        ul.first.wait_for(timeout=5000)
    except PlaywrightTimeoutError:
        print("  ⚠ No opciones (SKU fuera del ciclo?)")
        return False

    ver_todos = container.locator('[data-testid="autocomplete-button"]')
    if ver_todos.count() == 0:
        print("  ⚠ No 'Ver Todos los Resultados'")
        return False

    try:
        ver_todos.click()
    except:
        return False

    card = page.locator(f'[data-testid="card-{sku}"]')

    try:
        card.wait_for(state="visible", timeout=7000)
        return True
    except PlaywrightTimeoutError:
        print("  ⚠ No se encontró tarjeta")
        return False


def extract_card(page, sku: str, ciclo: str) -> Dict[str, Any] | None:
    card = page.locator(f'[data-testid="card-{sku}"]')
    if card.count() == 0:
        return None

    try:
        name = card.locator("[data-testid='card-name'] p").inner_text()
    except:
        name = None

    try:
        brand_line = card.locator("div[class*='CardDescription-brand'] p").inner_text()
        brand = brand_line.split("|")[0].strip()
    except:
        brand = None

    try:
        pts_block = card.locator(f"[data-testid='card-header-tag-points-{sku}']")
        pts_text = pts_block.inner_text()
        m = re.search(r"(\d+)\s*pts", pts_text)
        points = int(m.group(1)) if m else None
    except:
        points = None

    try:
        p_b = card.locator(f"[data-testid='purchasePrice-{sku}']")
        price_purchase = parse_price(p_b.inner_text())
    except:
        price_purchase = None

    try:
        r_b = card.locator(f"[data-testid='resalePrice-{sku}']")
        price_sale = parse_price(r_b.inner_text())
    except:
        price_sale = None

    try:
        image_url = card.locator("[data-testid='card-header-image'] img").get_attribute("src")
    except:
        image_url = None

    print(f"  ✔ {name} | Compra: {price_purchase} | Venta: {price_sale} | Pts: {points}")

    return {
        "brand": brand,
        "sku": sku,
        "name": name,
        "points": points,
        "price_purchase": price_purchase,
        "price_sale": price_sale,
        "image_url": image_url,
        "cycle": ciclo,
    }

# ======================================================
# RESUME + CHECKPOINTS
# ======================================================

def load_existing(path: Path) -> Dict[str, Dict]:
    if not path.exists():
        return {}
    try:
        arr = json.loads(path.read_text(encoding="utf-8"))
        return {prod["sku"]: prod for prod in arr}
    except:
        return {}


def save_results(data: Dict[str, Dict], missing: List[str], out_file: Path, missing_file: Path):
    arr = list(data.values())
    out_file.write_text(json.dumps(arr, indent=2, ensure_ascii=False), encoding="utf-8")
    missing_file.write_text(json.dumps(missing, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n💾 Checkpoint guardado:")
    print(f"   Productos: {len(arr)}")
    print(f"   Missing:   {len(missing)}")
    print("")

# ======================================================
# MAIN
# ======================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Archivo all_skus_<ciclo>.json")
    parser.add_argument("--cycle", required=True, help="Ciclo actual: 202518")
    args = parser.parse_args()

    ciclo = args.cycle
    input_file = Path(args.input)

    if not input_file.exists():
        raise FileNotFoundError(f"No existe archivo: {input_file}")

    # NOMBRES DINÁMICOS
    out_file = Path(f"output/data/catalogo_{ciclo}.json")
    missing_file = Path(f"output/data/missing_{ciclo}.json")

    skus = json.loads(input_file.read_text())
    print(f"📦 Total SKUs recibidos: {len(skus)}")

    # Resume
    resultados = load_existing(out_file)
    missing = load_existing(missing_file)

    remaining = [sku for sku in skus if sku not in resultados and sku not in missing]
    print(f"▶ Restantes por scrapear: {len(remaining)}")

    with sync_playwright() as p:
        print("\n🚀 Conectando a Chrome CDP en puerto 9222...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]

        # Detectar página de showcase
        page = None
        for pg in context.pages:
            if "showcase" in pg.url:
                page = pg
                print(f"✔ Controlando pestaña: {pg.url}")
                break

        if not page:
            print("❌ No hay pestaña con GSP abierto.")
            return

        # SCRAPE MASIVO
        for index, sku in enumerate(remaining, 1):
            print(f"\n========== [{index}/{len(remaining)}] SKU {sku} ==========")

            if detect_session_lost(page, sku):
                print("⛔ Sesión perdida — Deteniendo scraping.")
                break

            ok = search_and_open_results(page, sku)
            if not ok:
                missing[sku] = sku
                continue

            prod = extract_card(page, sku, ciclo)
            if prod:
                resultados[sku] = prod
            else:
                missing[sku] = sku

            if index % 50 == 0:
                save_results(resultados, list(missing.keys()), out_file, missing_file)

            time.sleep(random.uniform(0.6, 1.4))

        browser.close()

    save_results(resultados, list(missing.keys()), out_file, missing_file)
    print("\n✅ Scraping completo.")

if __name__ == "__main__":
    main()
