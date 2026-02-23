from pipeline.vision_extractor.normalize import normalize_item, normalize_page_json


EXPECTED_KEYS = {
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


def test_normalize_item_schema_from_price_nested_with_badge_inside_price():
    raw = {
        "sku": 225606,
        "title": "Producto",
        "price": {
            "regular": 100,
            "sale": 55,
            "discount_badge": {"text": "Más del 45% de descuento", "percent": 45},
        },
        "discount_badge": {"text": "Más del 45% de descuento", "percent": 45},
    }
    item = normalize_item(raw)

    assert set(item.keys()) == EXPECTED_KEYS
    assert item["sku"] == "225606"
    assert item["prices"] == {"currency": "MXN", "regular": 100, "sale": 55}
    assert item["discount_badge"] == {
        "text": "Más del 45% de descuento",
        "percent": 45,
        "kind": "more_than",
    }


def test_normalize_item_schema_from_regular_price_sale_price():
    raw = {
        "sku": "ABC",
        "regular_price": 200,
        "sale_price": 160,
        "discount_badge": {"text": "Hasta 40% de descuento", "percent": 40},
    }
    item = normalize_item(raw)

    assert set(item.keys()) == EXPECTED_KEYS
    assert item["prices"] == {"currency": "MXN", "regular": 200, "sale": 160}
    assert item["discount_badge"]["kind"] == "up_to"


def test_normalize_item_schema_from_regular_sale_root_and_discount_object():
    raw = {
        "sku": "XYZ",
        "regular": 300,
        "sale": 240,
        "discount": {"text": "35% de descuento", "percent": 35},
    }
    item = normalize_item(raw)

    assert set(item.keys()) == EXPECTED_KEYS
    assert item["prices"] == {"currency": "MXN", "regular": 300, "sale": 240}
    assert item["discount_badge"] == {
        "text": "35% de descuento",
        "percent": 35,
        "kind": "exact",
    }


def test_normalize_page_json_exact_schema_for_all_items():
    raw_page = {
        "page": 14,
        "items": [
            {"sku": 1, "regular_price": 10, "sale_price": 8},
            {"sku": 2, "prices": {"regular": 20, "sale": 18}},
            {"sku": 3, "regular": 30, "sale": 25, "discount": "Hasta 20% de descuento"},
        ],
    }

    page = normalize_page_json(raw_page)
    assert set(page.keys()) == {"page", "items"}
    assert page["page"] == 14
    for item in page["items"]:
        assert set(item.keys()) == EXPECTED_KEYS
        assert set(item["prices"].keys()) == {"currency", "regular", "sale"}
        assert item["prices"]["currency"] == "MXN"


def test_normalize_item_without_visible_discount_returns_null_badge():
    raw = {"sku": "NO-DISC", "regular": 100, "sale": 90}
    item = normalize_item(raw)
    assert item["discount_badge"] is None
