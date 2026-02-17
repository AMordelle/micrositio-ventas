#!/usr/bin/env python3
# scripts/rescrape_missing.py

import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# -----------------------------
# CONFIG
# -----------------------------
CICLO = "202517"

CATALOGO_FILE = Path(f"output/data/catalogo_{CICLO}.json")
MISSING_FILE = Path(f"output/data/missing_{CICLO}.json")

CATALOGO_FINAL = Path(f"output/data/catalogo_{CICLO}_final.json")
MISSING_FINAL = Path(f"output/data/missing_{CICLO}_final.json")

# -----------------------------
# HELPERS reutilizados del scraper
# -----------------------------

import re

def parse_price(text: str) -> float | None:
    m = re.search(r"(\d[0-9\.,]*\d)", text)
    if not m:
        return None
    num = m.group(1)
    if "." in num and "," in num:
        dot = num.find(".")
        comma = num.find(",")
        if dot < comma:
            num = num.replace(".", "").replace(",", ".")
        else:
            num = num.replace(",", "")
        return float(num)
    if "," in num:
        parts = num.split(",")
        if len(parts[-1]) == 3:
            num = num.replace(",", "")
            return float(num)
        else:
            return float(num.replace(",", "."))
    if "." in num:
        parts = num.split(".")
        if len(parts[-1]) == 3:
            num = num.replace(".", "")
            return float(num)
        else:
            return float(num)
    return float(num)


def extract_card_from_page(page, sku: str) -> Dict[str, Any] | None:
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
        tag = card.locator(f"[data-testid='card-header-tag-points-{sku}']")
        pts_txt = tag.inner_text()
        m_pts = re.search(r"(\d+)\s*pts", pts_txt)
        points = int(m_pts.group(1)) if m_pts else None
    except:
        points = None

    try:
        purchase_block = card.locator(f"[data-testid='purchasePrice-{sku}']")
        price_purchase = parse_price(purchase_block.inner_text())
    except:
        price_purchase = None

    try:
        resale_block = card.locator(f"[data-testid='resalePrice-{sku}']")
        price_sale = parse_price(resale_block.inner_text())
    except:
        price_sale = None

    try:
        image_url = card.locator("[data-testid='card-header-image'] img").get_attribute("src")
    except:
        image_url = None

    print(f"     ✔ {name} | Compra: {price_purchase} | Venta: {price_sale} | Pts: {points}")

    return {
        "brand": brand,
        "sku": sku,
        "name": name,
        "points": points,
        "price_purchase": price_purchase,
        "price_sale": price_sale,
        "image_url": image_url,
        "cycle": CICLO
    }


def search_and_open(page, sku: str) -> bool:
    search_container = page.locator('[data-testid="autocomplete-search"]')
    if search_container.count() == 0:
        return False

    input_box = search_container.locator('input[data-testid="ds-input"]')

    try:
        input_box.fill("")
        input_box.fill(sku)
    except:
        return False

    ul_options = search_container.locator('[data-testid="ul-options"] li')

    try:
        ul_options.first.wait_for(timeout=7000)
    except PlaywrightTimeoutError:
        return False

    btn = search_container.locator('[data-testid="autocomplete-button"]')
    if btn.count() == 0:
        return False

    try:
        btn.click()
    except:
        return False

    # esperar tarjeta con timeout grande
    card = page.locator(f'[data-testid="card-{sku}"]')
    try:
        card.wait_for(state="visible", timeout=12000)
        return True
    except:
        return False


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("\n🔁 RESCRAPER — SEGUNDA VUELTA")
    print(f"📄 Leyendo catálogo: {CATALOGO_FILE}")
    print(f"📄 Leyendo missing:  {MISSING_FILE}")

    catalogo = {item["sku"]: item for item in json.loads(CATALOGO_FILE.read_text("utf-8"))}
    missing = json.loads(MISSING_FILE.read_text("utf-8"))

    print(f"📦 Productos actuales: {len(catalogo)}")
    print(f"❗ SKUs faltantes a revisar: {len(missing)}")

    if not missing:
        print("No hay SKUs faltantes. Nada que hacer.")
        return

    with sync_playwright() as p:
        print("🚀 Conectando a Chrome REAL con CDP...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]

        # detectar pestaña showcase
        page = None
        for pg in context.pages:
            if "showcase" in pg.url:
                page = pg
                break

        if not page:
            print("❌ No se encontró pestaña con showcase abierta.")
            return

        still_missing = []

        for sku in missing:
            print(f"\n========== Reintentando SKU {sku} ==========")

            found = False

            for attempt in range(1, 4):   # 3 intentos
                print(f"  🔄 Intento {attempt}/3...")

                ok = search_and_open(page, sku)
                if ok:
                    data = extract_card_from_page(page, sku)
                    if data:
                        catalogo[sku] = data
                        found = True
                        break

                time.sleep(random.uniform(1.5, 2.3))

            if not found:
                still_missing.append(sku)
                print(f"  ❌ No se encontró el SKU {sku} tras 3 intentos.")

        browser.close()

    # guardar resultados
    catalogo_list = list(catalogo.values())
    CATALOGO_FINAL.write_text(json.dumps(catalogo_list, indent=2, ensure_ascii=False), encoding="utf-8")
    MISSING_FINAL.write_text(json.dumps(still_missing, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n====================================")
    print("   🟢 RESCRAPER FINALIZADO")
    print(f"   ✔ Total productos: {len(catalogo_list)} → {CATALOGO_FINAL}")
    print(f"   ❗ SKUs aún faltantes: {len(still_missing)} → {MISSING_FINAL}")
    print("====================================\n")


if __name__ == "__main__":
    main()
