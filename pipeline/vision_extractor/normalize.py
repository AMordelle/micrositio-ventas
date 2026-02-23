import re
from typing import Any


def _to_number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        try:
            parsed = float(cleaned)
        except ValueError:
            return None
        if parsed.is_integer():
            return int(parsed)
        return parsed
    return None


def _normalize_discount_badge(item: dict[str, Any], price_regular: Any, price_sale_final: Any) -> dict[str, Any] | None:
    badge = item.get("discount_badge")
    if isinstance(badge, dict):
        return badge

    discount_text = item.get("discount")
    if isinstance(discount_text, str):
        match = re.search(r"(\d+)\s*%", discount_text)
        if match:
            percent = int(match.group(1))
            return {
                "style": "fixed",
                "text": discount_text.strip().upper(),
                "percent": percent,
            }

    if item.get("discount_style") == "calculated":
        regular = _to_number(price_regular)
        sale = _to_number(price_sale_final)
        if isinstance(regular, (int, float)) and isinstance(sale, (int, float)) and regular > 0:
            percent = round((1 - (sale / regular)) * 100)
            return {
                "style": "calculated",
                "text": f"{percent}% DE DESCUENTO",
                "percent": percent,
            }

    return None


def normalize_item(item: dict[str, Any], page_num: int | None = None) -> dict[str, Any]:
    price_regular = item.get("price_regular")
    if price_regular is None:
        price_regular = item.get("regular_price", item.get("regular"))

    price_sale_final = item.get("price_sale_final")
    if price_sale_final is None:
        price_sale_final = item.get("sale_price", item.get("sale"))

    warnings = item.get("warnings")
    if not isinstance(warnings, list):
        warnings = [] if warnings in (None, "") else [str(warnings)]

    normalized = {
        "sku": str(item["sku"]) if item.get("sku") not in (None, "") else None,
        "title": item.get("title"),
        "variant": item.get("variant"),
        "size": item.get("size"),
        "price_regular": _to_number(price_regular),
        "price_sale_final": _to_number(price_sale_final),
        "discount_badge": _normalize_discount_badge(item, price_regular, price_sale_final),
        "notes": item.get("notes"),
        "warnings": warnings,
        "trace": {"pages": [page_num]} if page_num is not None else {"pages": []},
    }
    return normalized


def normalize_page_json(page_json: dict[str, Any]) -> dict[str, Any]:
    page_num = page_json.get("page")
    items = page_json.get("items", [])
    if not isinstance(items, list):
        items = []

    normalized_items = [normalize_item(item, page_num=page_num) for item in items if isinstance(item, dict)]

    normalized_page = dict(page_json)
    normalized_page["page"] = page_num
    normalized_page["items"] = normalized_items
    return normalized_page
