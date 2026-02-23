import re
from typing import Any


_ITEM_KEYS = {
    "sku",
    "title",
    "variant",
    "size",
    "prices",
    "discount_badge",
    "points",
    "bullets",
    "description",
    "extra",
}


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
        return int(parsed) if parsed.is_integer() else parsed
    return None


def _to_int(value: Any) -> int | None:
    number = _to_number(value)
    if isinstance(number, int):
        return number
    if isinstance(number, float) and number.is_integer():
        return int(number)
    return None


def _to_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _get_price_candidates(item: dict[str, Any], key: str) -> Any:
    prices = item.get("prices")
    if isinstance(prices, dict) and key in prices:
        return prices.get(key)

    price_obj = item.get("price")
    if isinstance(price_obj, dict) and key in price_obj:
        return price_obj.get(key)

    legacy_map = {
        "regular": ["price_regular", "regular_price", "regular"],
        "sale": ["price_sale_final", "sale_price", "sale"],
    }
    for legacy_key in legacy_map[key]:
        if legacy_key in item:
            return item.get(legacy_key)
    return None


def _normalize_prices(item: dict[str, Any]) -> dict[str, Any]:
    currency = "MXN"
    prices = item.get("prices")
    if isinstance(prices, dict) and isinstance(prices.get("currency"), str) and prices.get("currency", "").strip():
        currency = prices["currency"].strip()

    return {
        "currency": currency,
        "regular": _to_number(_get_price_candidates(item, "regular")),
        "sale": _to_number(_get_price_candidates(item, "sale")),
    }


def _extract_discount_text_and_percent(item: dict[str, Any]) -> tuple[str | None, int | None]:
    badge = item.get("discount_badge")
    if isinstance(badge, dict):
        text = badge.get("text")
        percent = _to_int(badge.get("percent"))
        if isinstance(text, str) and text.strip():
            if percent is None:
                match = re.search(r"(\d+)\s*%", text)
                percent = int(match.group(1)) if match else None
            return text.strip(), percent

    discount_text = item.get("discount_text")
    if isinstance(discount_text, str) and discount_text.strip():
        match = re.search(r"(\d+)\s*%", discount_text)
        percent = int(match.group(1)) if match else None
        return discount_text.strip(), percent

    discount = item.get("discount")
    if isinstance(discount, dict):
        text = discount.get("text")
        percent = _to_int(discount.get("percent"))
        if isinstance(text, str) and text.strip():
            if percent is None:
                match = re.search(r"(\d+)\s*%", text)
                percent = int(match.group(1)) if match else None
            return text.strip(), percent

    if isinstance(discount, str) and discount.strip() and discount.strip().lower() != "calculated":
        match = re.search(r"(\d+)\s*%", discount)
        percent = int(match.group(1)) if match else None
        return discount.strip(), percent

    return None, None


def _discount_kind(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("á", "a")
    if "mas del" in lowered:
        return "more_than"
    if "hasta" in lowered:
        return "up_to"
    if re.search(r"\d+\s*%", lowered):
        return "exact"
    return "exact"


def _normalize_discount_badge(item: dict[str, Any]) -> dict[str, Any] | None:
    text, percent = _extract_discount_text_and_percent(item)
    if text is None:
        return None
    return {
        "text": text,
        "percent": percent,
        "kind": _discount_kind(text),
    }


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    extra = dict(item.get("extra", {})) if isinstance(item.get("extra"), dict) else {}
    for key, value in item.items():
        if key not in _ITEM_KEYS and key not in {
            "price",
            "price_regular",
            "price_sale_final",
            "regular_price",
            "sale_price",
            "regular",
            "sale",
            "discount",
            "discount_text",
            "warnings",
            "notes",
            "trace",
        }:
            extra[key] = value

    sku_value = item.get("sku")
    sku = str(sku_value) if sku_value not in (None, "") else ""

    return {
        "sku": sku,
        "title": item.get("title") if item.get("title") is not None else None,
        "variant": item.get("variant") if item.get("variant") is not None else None,
        "size": item.get("size") if item.get("size") is not None else None,
        "prices": _normalize_prices(item),
        "discount_badge": _normalize_discount_badge(item),
        "points": _to_int(item.get("points")),
        "bullets": _to_string_list(item.get("bullets")),
        "description": _to_string_list(item.get("description")),
        "extra": extra,
    }


def normalize_page_json(page_json: dict[str, Any], page_num: int | None = None) -> dict[str, Any]:
    page = page_json.get("page", page_num)
    if page is None:
        page = page_num if page_num is not None else 0

    items_raw = page_json.get("items", [])
    if not isinstance(items_raw, list):
        items_raw = []

    return {
        "page": int(page),
        "items": [normalize_item(item) for item in items_raw if isinstance(item, dict)],
    }
