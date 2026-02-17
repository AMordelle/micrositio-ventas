#!/usr/bin/env python3
# scripts/rescrape_missing.py

import json
import time
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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


def _extract_prices_from_text(text: str) -> List[float]:
    matches = re.findall(r"\d[0-9\.,]*\d", text or "")
    prices: List[float] = []
    for candidate in matches:
        parsed = parse_price(candidate)
        if parsed is not None:
            prices.append(parsed)
    return prices


def derive_sale_prices(price_values: List[float]) -> Dict[str, float | None]:
    unique: List[float] = []
    for val in price_values:
        if val not in unique:
            unique.append(val)

    regular = unique[0] if unique else None
    promo = unique[-1] if len(unique) > 1 else None
    final = promo if promo is not None else regular

    return {
        "price_sale_regular": regular,
        "price_sale_promo": promo,
        "price_sale_final": final,
        "price_sale": final,
    }


def extract_sale_prices(card, sku: str) -> Dict[str, float | None]:
    resale_block = card.locator(f"[data-testid='resalePrice-{sku}']")
    if resale_block.count() == 0:
        return {
            "price_sale_regular": None,
            "price_sale_promo": None,
            "price_sale_final": None,
            "price_sale": None,
        }

    try:
        text_nodes = resale_block.locator("p").all_inner_texts()
        if not text_nodes:
            text_nodes = [resale_block.inner_text()]
    except:
        text_nodes = []

    parsed_prices: List[float] = []
    for txt in text_nodes:
        parsed_prices.extend(_extract_prices_from_text(txt))

    if not parsed_prices:
        try:
            parsed_prices = _extract_prices_from_text(resale_block.inner_text())
        except:
            parsed_prices = []

    return derive_sale_prices(parsed_prices)


def extract_card_from_page(page, sku: str, ciclo: str) -> Dict[str, Any] | None:
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

    sale_prices = extract_sale_prices(card, sku)

    try:
        image_url = card.locator("[data-testid='card-header-image'] img").get_attribute("src")
    except:
        image_url = None

    print(
        "     ✔ "
        f"{name} | Compra: {price_purchase} | "
        f"Venta regular: {sale_prices['price_sale_regular']} | "
        f"Promo: {sale_prices['price_sale_promo']} | "
        f"Final: {sale_prices['price_sale_final']} | "
        f"Pts: {points}"
    )

    return {
        "brand": brand,
        "sku": sku,
        "name": name,
        "points": points,
        "price_purchase": price_purchase,
        **sale_prices,
        "image_url": image_url,
        "cycle": ciclo
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", required=True, help="Ciclo actual (ej. 202517)")
    args = parser.parse_args()

    ciclo = args.cycle
    catalogo_file = Path(f"output/data/catalogo_{ciclo}.json")
    missing_file = Path(f"output/data/missing_{ciclo}.json")
    catalogo_final = Path(f"output/data/catalogo_{ciclo}_final.json")
    missing_final = Path(f"output/data/missing_{ciclo}_final.json")

    print("\n🔁 RESCRAPER — SEGUNDA VUELTA")
    print(f"📄 Leyendo catálogo: {catalogo_file}")
    print(f"📄 Leyendo missing:  {missing_file}")

    catalogo = {item["sku"]: item for item in json.loads(catalogo_file.read_text("utf-8"))}
    missing = json.loads(missing_file.read_text("utf-8"))

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
                    data = extract_card_from_page(page, sku, ciclo)
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
    catalogo_final.write_text(json.dumps(catalogo_list, indent=2, ensure_ascii=False), encoding="utf-8")
    missing_final.write_text(json.dumps(still_missing, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n====================================")
    print("   🟢 RESCRAPER FINALIZADO")
    print(f"   ✔ Total productos: {len(catalogo_list)} → {catalogo_final}")
    print(f"   ❗ SKUs aún faltantes: {len(still_missing)} → {missing_final}")
    print("====================================\n")


if __name__ == "__main__":
    main()
