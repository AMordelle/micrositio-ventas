#!/usr/bin/env python3
import httpx
from selectolax.parser import HTMLParser
import json
from pathlib import Path
import time
import random
import re

CICLO = "202517"
INPUT_SKUS = Path("output/skus/all_skus_202517.json")
OUTPUT_FILE = Path(f"output/data/natura_{CICLO}_http.json")
OUTPUT_MISSING = Path(f"output/data/natura_{CICLO}_http_missing.txt")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-MX,es;q=0.9",
}

def human_wait():
    time.sleep(random.uniform(0.4, 1.2))

def parse_price(text: str):
    m = re.search(r"(\d+[\.,]\d{2})", text)
    return float(m.group(1).replace(",", ".")) if m else None

def extract_card(html: str, sku: str):
    tree = HTMLParser(html)

    card = tree.css_first(f'[data-testid="card-{sku}"]')
    if not card:
        return None

    # Imagen
    img = card.css_first("img")
    image_url = img.attributes.get("src") if img else None

    # Marca + SKU
    brand_line = card.css_first(".CardDescription-brand-7-2-2701 p")
    brand_line = brand_line.text(strip=True) if brand_line else None

    # Nombre
    name_el = card.css_first('[data-testid="card-name"] p')
    name = name_el.text(strip=True) if name_el else None

    # Puntos
    pts_el = card.css_first('[data-testid^="card-header-tag-points"]')
    pts_text = pts_el.text(strip=True) if pts_el else ""
    m_pts = re.search(r"(\d+)", pts_text)
    points = int(m_pts.group(1)) if m_pts else None

    # Precios
    purchase_el = card.css_first('[data-testid^="purchasePrice"] p:last-child')
    resale_el = card.css_first('[data-testid^="resalePrice"] p:last-child')

    purchase = parse_price(purchase_el.text(strip=True)) if purchase_el else None
    resale = parse_price(resale_el.text(strip=True)) if resale_el else None

    return {
        "brand": brand_line.split("|")[0].strip() if brand_line else None,
        "sku": sku,
        "name": name,
        "points": points,
        "price_purchase": purchase,
        "price_sale": resale,
        "image_url": image_url,
        "cycle": CICLO,
        "category": None,
    }

def main():
    data = json.loads(INPUT_SKUS.read_text())

    skus = data["skus"] if "skus" in data else data
    skus = [str(s).strip() for s in skus]

    client = httpx.Client(headers=HEADERS, timeout=20)

    results = []
    missing = []

    for index, sku in enumerate(skus, start=1):
        print(f"\n[{index}/{len(skus)}] SKU {sku}")

        url = f"https://gsp.natura.com/showcase/pesquisa?q={sku}&ciclo={CICLO}"
        print(" →", url)

        try:
            resp = client.get(url)
        except Exception as e:
            print(" ⚠ Error HTTP:", e)
            missing.append(sku)
            continue

        card = extract_card(resp.text, sku)
        if not card:
            print(" ⚠ No se encontró tarjeta")
            missing.append(sku)
        else:
            print(" ✔", card["name"])
            results.append(card)

        human_wait()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    OUTPUT_MISSING.write_text("\n".join(missing))

    print("\n==== FINALIZADO ====")
    print("Productos:", len(results))
    print("Faltantes:", len(missing))

if __name__ == "__main__":
    main()
